# SPDX-License-Identifier: Apache-2.0
"""Safe, provider-neutral verification of supplied external evidence bundles."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
import io
import math
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Any
from zipfile import BadZipFile, ZipFile, is_zipfile

from .language import E7QError
from .openqasm2 import import_openqasm2
from .temporal import temporal_evidence


SCHEMA = "e7q.external-evidence-receipt/v1alpha1"

_MAX_ARCHIVE_BYTES = 128 * 1024 * 1024
_MAX_FILES = 512
_MAX_FILE_BYTES = 32 * 1024 * 1024
_MAX_TOTAL_BYTES = 128 * 1024 * 1024
_MAX_COMPRESSION_RATIO = 200
_REQUIRED_RECORD_FILES = {
    "calibration.json",
    "final_circuit.qasm",
    "job_metadata.json",
    "mapping.json",
    "raw_counts.json",
    "versions.json",
}
_TWO_QUBIT_GATES = {"cx", "cz", "ecr", "rzz", "swap"}
_IR_GATE_NAMES = {
    "cnot": "cx",
    "hadamard": "h",
    "measure": "measure",
    "pauli_x": "x",
    "pauli_y": "y",
    "pauli_z": "z",
    "phase": "rz",
}


def _digest(value: bytes) -> str:
    return "sha256:" + sha256(value).hexdigest()


def _member_name(value: str) -> str:
    if not value or "\x00" in value or "\\" in value:
        raise E7QError("external bundle contains an unsafe member name")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in value.split("/")):
        raise E7QError(f"external bundle contains an unsafe member: {value}")
    if path.parts and path.parts[0].endswith(":"):
        raise E7QError(f"external bundle contains an unsafe member: {value}")
    return path.as_posix()


@dataclass(frozen=True)
class _Source:
    kind: str
    digest: str
    members: dict[str, bytes]
    total_bytes: int


def _load_zip(path: Path) -> _Source:
    members: dict[str, bytes] = {}
    total = 0
    try:
        if path.stat().st_size > _MAX_ARCHIVE_BYTES:
            raise E7QError("external bundle archive exceeds the size limit")
        with path.open("rb") as stream:
            archive_bytes = stream.read(_MAX_ARCHIVE_BYTES + 1)
        if len(archive_bytes) > _MAX_ARCHIVE_BYTES:
            raise E7QError("external bundle archive exceeds the size limit")
        # Digest and inspect the same bounded snapshot, not two file reads.
        with ZipFile(io.BytesIO(archive_bytes)) as archive:
            infos = archive.infolist()
            if len(infos) > _MAX_FILES:
                raise E7QError(f"external bundle exceeds {_MAX_FILES} members")
            seen: set[str] = set()
            for info in infos:
                original = info.orig_filename
                name = _member_name(original[:-1] if original.endswith("/") else original)
                if name in seen:
                    raise E7QError(f"external bundle contains a duplicate member: {name}")
                seen.add(name)
                mode = (info.external_attr >> 16) & 0xFFFF
                if stat.S_ISLNK(mode):
                    raise E7QError(f"external bundle contains a symlink: {name}")
                if info.flag_bits & 0x1:
                    raise E7QError(f"external bundle contains an encrypted member: {name}")
                if info.is_dir():
                    continue
                if info.file_size > _MAX_FILE_BYTES:
                    raise E7QError(f"external bundle member is too large: {name}")
                total += info.file_size
                if total > _MAX_TOTAL_BYTES:
                    raise E7QError("external bundle expands beyond the size limit")
                if (
                    info.file_size > 1024 * 1024
                    and info.compress_size > 0
                    and info.file_size / info.compress_size > _MAX_COMPRESSION_RATIO
                ):
                    raise E7QError(
                        f"external bundle member has an unsafe compression ratio: {name}"
                    )
                members[name] = archive.read(info)
    except (BadZipFile, OSError, RuntimeError, NotImplementedError) as exc:
        raise E7QError(f"invalid external bundle ZIP: {exc}") from exc
    return _Source("zip", _digest(archive_bytes), members, total)


def _load_directory(path: Path) -> _Source:
    root = path.resolve()
    if path.is_symlink():
        raise E7QError("external bundle directory must not be a symlink")
    members: dict[str, bytes] = {}
    total = 0
    for candidate in sorted(root.rglob("*")):
        if candidate.is_symlink():
            raise E7QError(f"external bundle contains a symlink: {candidate}")
        if not candidate.is_file():
            continue
        name = _member_name(candidate.relative_to(root).as_posix())
        size = candidate.stat().st_size
        if size > _MAX_FILE_BYTES:
            raise E7QError(f"external bundle member is too large: {name}")
        total += size
        if len(members) >= _MAX_FILES or total > _MAX_TOTAL_BYTES:
            raise E7QError("external bundle directory exceeds the safety limits")
        members[name] = candidate.read_bytes()
    canonical = sha256()
    for name, content in sorted(members.items()):
        canonical.update(name.encode("utf-8"))
        canonical.update(b"\0")
        canonical.update(sha256(content).digest())
    return _Source(
        "directory",
        "sha256:" + canonical.hexdigest(),
        members,
        total,
    )


def _load_source(path: str | Path) -> _Source:
    source = Path(path)
    if source.is_dir():
        return _load_directory(source)
    if source.is_file() and is_zipfile(source):
        return _load_zip(source)
    raise E7QError("external bundle must be a ZIP archive or directory")


def _check(
    checks: list[dict[str, object]],
    name: str,
    passed: bool,
    *,
    severity: str = "error",
    detail: str | None = None,
) -> None:
    value: dict[str, object] = {
        "name": name,
        "passed": bool(passed),
        "severity": severity,
    }
    if detail is not None:
        value["detail"] = detail
    checks.append(value)


def _record_member(prefix: str, filename: str) -> str:
    return f"{prefix}/{filename}" if prefix else filename


def _unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _finite_json_float(text):
    value = float(text)
    if not math.isfinite(value):
        raise ValueError("non-finite JSON number")
    return value


def _reject_json_constant(text):
    raise ValueError(f"invalid JSON constant: {text}")


def _json_object(
    members: dict[str, bytes],
    prefix: str,
    filename: str,
    checks: list[dict[str, object]],
) -> dict[str, Any] | None:
    name = _record_member(prefix, filename)
    raw = members.get(name)
    if raw is None:
        return None
    try:
        value = json.loads(raw, object_pairs_hook=_unique_json_object,
                           parse_float=_finite_json_float,
                           parse_constant=_reject_json_constant)
    except (ValueError, UnicodeDecodeError, RecursionError) as exc:
        _check(checks, f"json:{filename}", False, detail=str(exc))
        return None
    if not isinstance(value, dict):
        _check(checks, f"json:{filename}", False, detail="must be a JSON object")
        return None
    _check(checks, f"json:{filename}", True)
    return value


def _timestamp_is_valid(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _parse_qasm(raw: bytes) -> dict[str, object]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("OpenQASM must be UTF-8 text") from exc
    imported = import_openqasm2(text)
    quantum = imported["registers"]["quantum"]
    classical = imported["registers"]["classical"]
    if len(quantum) != 1 or len(classical) != 1:
        raise ValueError("external bundle profile requires one qreg and one creg")
    qname, qreg_width = quantum[0]["name"], quantum[0]["width"]
    cname, creg_width = classical[0]["name"], classical[0]["width"]
    instructions: list[dict[str, object]] = []
    for operation in imported["operations"]:
        qubits = operation.get("qubits", [])
        if any(item["register"] != qname for item in qubits):
            raise ValueError("external bundle operations must use the declared qreg")
        instructions.append({
            "name": operation["name"],
            "qubits": [item["index"] for item in qubits],
        })
    measurements = []
    for item in imported["measurements"]:
        if item["qubit"]["register"] != qname or item["clbit"]["register"] != cname:
            raise ValueError("external bundle measurements use an unexpected register")
        measurements.append({
            "physical_qubit": item["qubit"]["index"],
            "clbit": item["clbit"]["index"],
        })
    measurements.sort(key=lambda item: item["clbit"])
    active = sorted({qubit for item in instructions for qubit in item["qubits"]})
    return {
        "qreg_width": qreg_width,
        "creg_width": creg_width,
        "operations": imported["operation_counts"],
        "instructions": instructions,
        "measurements": measurements,
        "active_qubits": active,
        "two_qubit_edges": sorted(
            {
                (str(instruction["name"]), *instruction["qubits"])
                for instruction in instructions
                if instruction["name"] in _TWO_QUBIT_GATES
                and len(instruction["qubits"]) == 2
            }
        ),
        "unsupported": [],
    }


def _manifest_rows(raw: bytes) -> list[tuple[str, str]]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return []
    rows: list[tuple[str, str]] = []
    for line in text.splitlines():
        if "`" not in line or "|" not in line:
            continue
        fields = line.strip().strip("|").split("|")
        if len(fields) < 3:
            continue
        file_match = re.search(r"`([^`]+)`", fields[0])
        hash_match = re.search(r"`(?:sha256:)?([0-9a-fA-F]{8,64})(?:…|\.\.\.)?`", fields[-1])
        if file_match and hash_match:
            rows.append((file_match.group(1), hash_match.group(1).lower()))
    return rows


def _validate_manifest(
    members: dict[str, bytes],
    prefix: str,
    checks: list[dict[str, object]],
) -> str:
    name = _record_member(prefix, "MANIFEST.md")
    raw = members.get(name)
    if raw is None:
        _check(
            checks,
            "manifest-present",
            False,
            severity="warning",
            detail="no MANIFEST.md was supplied",
        )
        return "PARTIAL"
    rows = _manifest_rows(raw)
    _check(checks, "manifest-readable", bool(rows), detail="no digest rows found")
    if not rows:
        return "FAIL"
    all_match = True
    full_hashes = True
    listed: set[str] = set()
    for filename, declared in rows:
        try:
            relative = _member_name(filename)
        except E7QError:
            _check(
                checks,
                f"manifest-member:{filename}",
                False,
                detail="unsafe manifest path",
            )
            all_match = False
            continue
        listed.add(relative)
        content = members.get(_record_member(prefix, relative))
        matches = content is not None and sha256(content).hexdigest().startswith(declared)
        _check(checks, f"manifest-digest:{relative}", matches)
        all_match = all_match and matches
        full_hashes = full_hashes and len(declared) == 64
    _check(
        checks,
        "manifest-full-sha256",
        full_hashes,
        severity="warning",
        detail=(None if full_hashes else "one or more digests are abbreviated"),
    )
    coverage = _REQUIRED_RECORD_FILES <= listed
    _check(
        checks,
        "manifest-required-file-coverage",
        coverage,
        severity="warning",
    )
    if not all_match:
        return "FAIL"
    return "PASS" if full_hashes and coverage else "PARTIAL"


def _validate_record(
    source: _Source,
    prefix: str,
    *,
    include_counts: bool,
) -> dict[str, object]:
    members = source.members
    checks: list[dict[str, object]] = []
    present = {
        PurePosixPath(name).name
        for name in members
        if PurePosixPath(name).parent.as_posix() == (prefix or ".")
    }
    for filename in sorted(_REQUIRED_RECORD_FILES):
        _check(checks, f"required-file:{filename}", filename in present)

    integrity = _validate_manifest(members, prefix, checks)
    metadata = _json_object(members, prefix, "job_metadata.json", checks)
    counts_value = _json_object(members, prefix, "raw_counts.json", checks)
    mapping = _json_object(members, prefix, "mapping.json", checks)
    calibration = _json_object(members, prefix, "calibration.json", checks)
    versions = _json_object(members, prefix, "versions.json", checks)
    ir = _json_object(members, prefix, "hieroglyphs_ir.json", checks)

    record_name = PurePosixPath(prefix).name if prefix else "external-record"
    circuit_name = record_name
    job_id: str | None = None
    backend: str | None = None
    shots: int | None = None
    completion: str | None = None
    if metadata is not None:
        circuit_name = str(metadata.get("circuit_name") or record_name)
        job_id = metadata.get("job_id") if isinstance(metadata.get("job_id"), str) else None
        backend = metadata.get("backend") if isinstance(metadata.get("backend"), str) else None
        raw_shots = metadata.get("shots")
        shots = (
            raw_shots
            if isinstance(raw_shots, int) and not isinstance(raw_shots, bool)
            else None
        )
        _check(checks, "metadata:job-id", bool(job_id))
        _check(checks, "metadata:backend", bool(backend))
        _check(checks, "metadata:shots", shots is not None and shots > 0)
        status = metadata.get("status")
        _check(checks, "metadata:status-type", isinstance(status, str))
        _check(
            checks,
            "metadata:terminal-status",
            isinstance(status, str) and status in {"DONE", "COMPLETED", "SUCCESS"},
            severity="warning",
            detail=f"reported status: {status!r}",
        )
        for field in ("completion_time_utc", "completed_at", "completion_date"):
            if field in metadata:
                completion = str(metadata[field])
                break
        _check(
            checks,
            "metadata:completion-time",
            completion is not None and _timestamp_is_valid(completion),
            severity="warning",
            detail="provider-reported and not authenticated",
        )

    normalized_counts: dict[str, int] = {}
    outcome_width: int | None = None
    count_total: int | None = None
    if counts_value is not None:
        raw_counts = counts_value.get("counts")
        valid_counts = isinstance(raw_counts, dict) and bool(raw_counts)
        if valid_counts:
            widths: set[int] = set()
            for outcome, count in raw_counts.items():
                if (
                    not isinstance(outcome, str)
                    or not outcome
                    or set(outcome) - {"0", "1"}
                    or not isinstance(count, int)
                    or isinstance(count, bool)
                    or count < 0
                ):
                    valid_counts = False
                    break
                widths.add(len(outcome))
                normalized_counts[outcome] = count
            valid_counts = valid_counts and len(widths) == 1
            if valid_counts:
                outcome_width = next(iter(widths))
                count_total = sum(normalized_counts.values())
        _check(checks, "counts:binary-nonnegative-equal-width", valid_counts)
        if valid_counts:
            _check(checks, "counts:sum-to-shots", shots is not None and count_total == shots)
            _check(
                checks,
                "counts:declared-total",
                type(counts_value.get("total_shots")) is int and counts_value["total_shots"] == count_total,
            )
            _check(
                checks,
                "counts:declared-unique",
                type(counts_value.get("num_unique_bitstrings")) is int and counts_value["num_unique_bitstrings"] == len(normalized_counts),
            )

    qasm: dict[str, object] | None = None
    qasm_raw = members.get(_record_member(prefix, "final_circuit.qasm"))
    if qasm_raw is not None:
        try:
            qasm = _parse_qasm(qasm_raw)
        except ValueError as exc:
            _check(checks, "qasm:parse", False, detail=str(exc))
        else:
            _check(checks, "qasm:parse", True)
            _check(
                checks,
                "qasm:supported-statements",
                not qasm["unsupported"],
                detail=(str(qasm["unsupported"][:3]) if qasm["unsupported"] else None),
            )

    if qasm is not None and metadata is not None:
        _check(
            checks,
            "qasm:declared-registers",
            isinstance(qasm["qreg_width"], int)
            and qasm["qreg_width"] > 0
            and isinstance(qasm["creg_width"], int)
            and qasm["creg_width"] > 0,
        )
        _check(
            checks,
            "qasm:device-width",
            type(metadata.get("num_qubits_device")) is int
            and qasm["qreg_width"] == metadata["num_qubits_device"],
        )
        _check(
            checks,
            "qasm:outcome-width",
            outcome_width is not None and qasm["creg_width"] == outcome_width,
        )
        declared_ops = metadata.get("op_counts")
        normalized_ops = (
            {str(name).lower(): value for name, value in declared_ops.items()}
            if isinstance(declared_ops, dict)
            and all(isinstance(name, str) and type(value) is int and value >= 0
                    for name, value in declared_ops.items())
            and len({name.lower() for name in declared_ops}) == len(declared_ops)
            else None
        )
        _check(checks, "qasm:operation-counts", qasm["operations"] == normalized_ops)

    mapping_summary: dict[str, object] = {}
    if mapping is not None:
        raw_map = mapping.get("measurement_map")
        valid_map = isinstance(raw_map, list) and bool(raw_map)
        normalized_map: list[dict[str, int]] = []
        if valid_map:
            for item in raw_map:
                if (
                    not isinstance(item, dict)
                    or not isinstance(item.get("clbit"), int)
                    or isinstance(item.get("clbit"), bool)
                    or not isinstance(item.get("physical_qubit"), int)
                    or isinstance(item.get("physical_qubit"), bool)
                ):
                    valid_map = False
                    break
                normalized_map.append(
                    {"clbit": item["clbit"], "physical_qubit": item["physical_qubit"]}
                )
            normalized_map.sort(key=lambda item: item["clbit"])
            valid_map = (
                valid_map
                and len({item["clbit"] for item in normalized_map}) == len(normalized_map)
                and len({item["physical_qubit"] for item in normalized_map})
                == len(normalized_map)
            )
        _check(checks, "mapping:measurement-map", valid_map)
        if valid_map:
            expected_clbits = list(range(len(normalized_map)))
            _check(
                checks,
                "mapping:complete-clbits",
                [item["clbit"] for item in normalized_map] == expected_clbits,
            )
            _check(
                checks,
                "mapping:outcome-width",
                outcome_width is not None
                and type(mapping.get("num_clbits")) is int
                and mapping["num_clbits"] == outcome_width == len(normalized_map),
            )
            if qasm is not None:
                _check(checks, "mapping:qasm-measurements", qasm["measurements"] == normalized_map)
        active = mapping.get("active_qubits")
        valid_active = (
            isinstance(active, list)
            and all(isinstance(item, int) and not isinstance(item, bool) for item in active)
            and len(active) == len(set(active))
        )
        _check(checks, "mapping:active-qubits", valid_active)
        device_width = mapping.get("device_num_qubits")
        active_in_range = (
            valid_active
            and isinstance(device_width, int)
            and not isinstance(device_width, bool)
            and device_width > 0
            and all(0 <= item < device_width for item in active)
        )
        _check(checks, "mapping:active-qubits-in-device-range", active_in_range)
        _check(
            checks,
            "mapping:declared-active-count",
            valid_active and type(mapping.get("num_active_qubits")) is int
            and mapping["num_active_qubits"] == len(active),
        )
        if valid_active and qasm is not None:
            _check(checks, "mapping:qasm-active-qubits", sorted(active) == qasm["active_qubits"])
            _check(
                checks,
                "mapping:qasm-device-width",
                device_width == qasm["qreg_width"],
            )
        mapping_summary = {
            "num_clbits": mapping.get("num_clbits"),
            "device_num_qubits": mapping.get("device_num_qubits"),
            "active_qubits": active if valid_active else None,
            "measurement_map": normalized_map if valid_map else None,
        }

    if calibration is not None and qasm is not None and mapping is not None:
        calibrated_qubits = calibration.get("qubits")
        active = mapping.get("active_qubits")
        coverage = (
            isinstance(calibrated_qubits, dict)
            and isinstance(active, list)
            and {str(item) for item in active} <= set(calibrated_qubits)
        )
        _check(checks, "calibration:active-qubit-coverage", coverage)
        gate_errors = calibration.get("gate_errors_sample")
        missing_edges: list[str] = []
        if isinstance(gate_errors, dict):
            for gate, first, second in qasm["two_qubit_edges"]:
                direct = f"{gate}_{first}_{second}"
                reverse = f"{gate}_{second}_{first}"
                if direct not in gate_errors and reverse not in gate_errors:
                    missing_edges.append(direct)
        elif qasm["two_qubit_edges"]:
            missing_edges = ["calibration gate_errors_sample is absent"]
        _check(
            checks,
            "calibration:two-qubit-edge-coverage",
            not missing_edges,
            severity="warning",
            detail=(", ".join(missing_edges[:8]) if missing_edges else None),
        )

    if ir is not None:
        gates = ir.get("gates")
        valid_ir = isinstance(gates, list) and type(ir.get("num_gates")) is int and ir["num_gates"] == len(gates)
        _check(checks, "ir:declared-gate-count", valid_ir)
        explicit_destinations = False
        if isinstance(gates, list):
            for gate in gates:
                if isinstance(gate, dict) and str(gate.get("gate_type")).lower() == "measure":
                    explicit_destinations = explicit_destinations or any(
                        key in gate for key in ("clbit", "clbits", "classical_bits")
                    )
        _check(
            checks,
            "ir:explicit-measurement-destinations",
            explicit_destinations,
            severity="warning",
        )
        pre_raw = members.get(_record_member(prefix, "pre_transpile_circuit.qasm"))
        if valid_ir and pre_raw is not None:
            try:
                pre = _parse_qasm(pre_raw)
            except ValueError:
                _check(checks, "ir:pre-qasm-alignment", False, severity="warning")
            else:
                ir_signature = []
                for gate in gates:
                    if not isinstance(gate, dict):
                        continue
                    name = str(gate.get("gate_type", "")).lower()
                    name = _IR_GATE_NAMES.get(name, name)
                    qubits = gate.get("qubits")
                    ir_signature.append((name, qubits))
                pre_signature = [
                    (instruction["name"], instruction["qubits"])
                    for instruction in pre["instructions"]
                ]
                _check(
                    checks,
                    "ir:pre-qasm-alignment",
                    ir_signature == pre_signature,
                    severity="warning",
                    detail="gate names and qubit operands only; parameters are not compared",
                )

    build = None
    if metadata is not None:
        build = metadata.get("hieroglyphs_build")
    if build is None and versions is not None:
        build = versions.get("hieroglyphs_compiler")
    stable_build = isinstance(build, str) and "repo-local" not in build.lower()
    _check(
        checks,
        "reproducibility:stable-compiler-build",
        stable_build,
        severity="warning",
        detail=f"reported build: {build!r}",
    )

    record_files = {
        PurePosixPath(name).name: {
            "digest": _digest(content),
            "size_bytes": len(content),
        }
        for name, content in sorted(members.items())
        if PurePosixPath(name).parent.as_posix() == (prefix or ".")
    }
    has_errors = any(not check["passed"] and check["severity"] == "error" for check in checks)
    warnings = [
        check["name"]
        for check in checks
        if not check["passed"] and check["severity"] == "warning"
    ]
    counts_summary: dict[str, object] = {
        "digest": (
            _digest(members[_record_member(prefix, "raw_counts.json")])
            if _record_member(prefix, "raw_counts.json") in members
            else None
        ),
        "shots": count_total,
        "unique_outcomes": len(normalized_counts) if normalized_counts else None,
        "outcome_width": outcome_width,
    }
    if include_counts and normalized_counts:
        counts_summary["values"] = dict(sorted(normalized_counts.items()))
    return {
        "record_path": prefix or ".",
        "circuit_name": circuit_name,
        "job_id": job_id,
        "backend": backend,
        "reported_completion": completion,
        "status": "PASS" if not has_errors else "FAIL",
        "integrity": integrity,
        "counts": counts_summary,
        "qasm": (
            {
                "digest": _digest(qasm_raw),
                "declared_device_width": qasm["qreg_width"],
                "classical_width": qasm["creg_width"],
                "active_qubits": qasm["active_qubits"],
                "operation_counts": qasm["operations"],
            }
            if qasm is not None and qasm_raw is not None
            else None
        ),
        "mapping": mapping_summary,
        "compiler_build": build,
        "files": record_files,
        "checks": checks,
        "warnings": warnings,
    }


def _worst(values: list[str]) -> str:
    order = {"PASS": 0, "PARTIAL": 1, "FAIL": 2}
    return max(values, key=lambda value: order[value]) if values else "FAIL"


def verify_external_bundle(
    path: str | Path,
    *,
    include_counts: bool = False,
) -> dict[str, object]:
    """Verify a supplied ZIP/directory and emit a deterministic bounded receipt."""
    source = _load_source(path)
    metadata_members = sorted(
        name for name in source.members if PurePosixPath(name).name == "job_metadata.json"
    )
    if not metadata_members:
        raise E7QError("external bundle contains no job_metadata.json records")
    prefixes = [
        (
            ""
            if PurePosixPath(name).parent.as_posix() == "."
            else PurePosixPath(name).parent.as_posix()
        )
        for name in metadata_members
    ]
    circuits = [
        _validate_record(source, prefix, include_counts=include_counts)
        for prefix in prefixes
    ]
    integrity = _worst([str(circuit["integrity"]) for circuit in circuits])
    internal = "PASS" if all(circuit["status"] == "PASS" for circuit in circuits) else "FAIL"
    overall = "PASS" if integrity != "FAIL" and internal == "PASS" else "FAIL"
    job_groups: dict[str, list[dict[str, object]]] = {}
    for circuit in circuits:
        key = str(circuit["job_id"] or "unidentified")
        job_groups.setdefault(key, []).append(circuit)
    jobs = []
    for job_id, records in sorted(job_groups.items()):
        jobs.append(
            {
                "job_id": job_id,
                "records": len(records),
                "circuits": [record["circuit_name"] for record in records],
                "backends": sorted({str(record["backend"]) for record in records}),
                "shared_mapping": len(
                    {
                        json.dumps(record["mapping"], sort_keys=True)
                        for record in records
                    }
                ) == 1,
            }
        )
    reported_times = sorted(
        {
            str(circuit["reported_completion"])
            for circuit in circuits
            if circuit["reported_completion"] is not None
        }
    )
    judgments = {
        "archive_safety": {
            "status": "PASS",
            "basis": "bounded in-memory inspection; no archive member was executed",
        },
        "artifact_integrity": {
            "status": integrity,
            "basis": "manifest digests checked against the received member bytes",
        },
        "internal_consistency": {
            "status": internal,
            "basis": "cross-file structural, arithmetic, QASM, mapping, and calibration checks",
        },
        "external_provenance": {
            "status": "PARTIAL",
            "basis": (
                "provider identifiers and timestamps are supplied records, "
                "not independently authenticated"
            ),
        },
        "reproducibility": {
            "status": "PARTIAL",
            "basis": (
                "submitted circuit artifacts are retained, but external compilation "
                "and hardware execution are not fully reproduced"
            ),
        },
        "algorithmic_claim_validation": {
            "status": "NOT_EVALUATED",
            "basis": (
                "bundle verification does not assess QFT, QEC, fidelity, or other "
                "algorithm-specific claims"
            ),
        },
    }
    conformance = (
        "INTERNALLY_CONSISTENT_WITH_LIMITATIONS" if overall == "PASS" else "NONCONFORMANT"
    )
    return {
        "schema": SCHEMA,
        "status": overall,
        "conformance": conformance,
        "validation_scope": "offline-external-bundle",
        "source": {
            "kind": source.kind,
            "digest": source.digest,
            "file_count": len(source.members),
            "uncompressed_bytes": source.total_bytes,
        },
        "records": len(circuits),
        "jobs": jobs,
        "circuits": circuits,
        "judgments": judgments,
        "temporal_evidence": temporal_evidence(
            temporal_order_roles=["TD0", "TD1"],
            carrier_ref=source.digest,
            carrier_description="one supplied external execution-evidence package",
            order_relation="reported compilation, submission, and completion record order",
            chronology_status="provider-reported-not-authenticated",
            projection_from="supplied external archive or directory",
            projection_to="normalized E7Q external-evidence receipt",
            preserves=[
                "received member and source digests",
                "reported job identities and completion fields",
                "counts, circuit, mapping, and calibration consistency checks",
            ],
            loses=[
                "provider-authenticated chronology",
                "shot-level execution history",
                "unrecorded compiler and provider state",
            ],
            reconstruction_status="partial",
            reconstruction_limit=(
                "The receipt reconstructs only the supplied artifact relations; it does "
                "not authenticate or uniquely reconstruct provider execution."
            ),
            clock={
                "field": "job_metadata completion fields",
                "value": reported_times,
                "status": "provider-reported-not-authenticated",
            },
            criterion_id="e7q.external-bundle-consistency",
            criterion_edition="1alpha1",
            criterion_parameters={"include_counts": include_counts},
            criterion="safe ingestion and internal evidence consistency",
            phase=overall,
            boundary_crossing={"detected": False},
        ),
        "limitations": [
            (
                "The receipt does not authenticate the provider, job, timestamps, "
                "calibration, or submitter."
            ),
            (
                "QPY files are identified by digest but are not semantically decoded "
                "by the dependency-free verifier."
            ),
            "Reported circuit depth is not independently recomputed.",
            "Algorithmic correctness and physical fidelity are outside this verification scope.",
        ],
        "proof": [
            {
                "step": 0,
                "kind": "source-identity",
                "source_digest": source.digest,
                "source_kind": source.kind,
                "archive_safety": "PASS",
            },
            {
                "step": 1,
                "kind": "record-discovery",
                "records": len(circuits),
                "jobs": len(jobs),
            },
            {
                "step": 2,
                "kind": "integrity-and-consistency",
                "artifact_integrity": integrity,
                "internal_consistency": internal,
            },
            {
                "step": 3,
                "kind": "bounded-verdict",
                "status": overall,
                "conformance": conformance,
            },
            {
                "step": 4,
                "kind": "evidence-boundary",
                "boundary": (
                    "PASS is limited to safe ingestion and internal consistency of "
                    "the received artifacts. It is not provider authentication, "
                    "algorithm validation, hardware certification, or fidelity evidence."
                ),
            },
        ],
    }
