# SPDX-License-Identifier: Apache-2.0
"""Offline linkage of a unique planning selection to supplied legacy bytes.

This product-local adapter certifies internal consistency and byte commitments,
not program equivalence, provider authentication or physical execution. It never
resolves identities through storage and never invokes F2 or execution engines.
"""
from __future__ import annotations

from hashlib import sha256
import json
import math
import re
from typing import Any

from .canonical import canonical_bytes, identified_digest
from .conformance import validate_graph
from .legacy_receipt_workflow import (
    SOURCE_ADAPTER,
    WORKFLOW_FORMAT,
    recover_legacy_source,
    validate_legacy_receipt_evidence,
)
from .realisation import (
    RealisationError,
    assess_realisation,
    validate_realisation_request,
    validate_realisation_result,
)

PROFILE = "e7q.ir.selected-legacy-receipt-binding/v0alpha1"
KERNEL_COMMIT = "fc4cdf95c6434e653efbe017587aab60b4b2a86c"
EDITIONS = {
    "family": "e7q.ir.candidate-family/v0alpha1",
    "history": "e7q.ir.transformation-history/v0alpha1",
    "realisation": "e7q.ir.realisation-result/v0alpha1",
    "rgp": "RGP2@v0.12.1-experimental",
}
REQUEST_SCHEMA = "e7q.ir.receipt-binding-request/v0alpha1"
RESULT_SCHEMA = "e7q.ir.receipt-binding-result/v0alpha1"
LAYER_SCHEMA = "e7q.ir.receipt-binding-layer/v0alpha1"
EDGE_SCHEMA = "e7q.ir.receipt-binding-edge/v0alpha1"
WITNESS_SCHEMA = "e7q.ir.receipt-binding-witness/v0alpha1"
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_CEILINGS = {
    "max_graph_bytes": 16 * 1024 * 1024,
    "max_artifacts": 64,
    "max_relations": 128,
    "max_source_bytes": 1048576,
}
_MESSAGES = {
    "bound": "Selected member is linked to supplied internally consistent receipt evidence.",
    "unbound": "No unique member is available for receipt binding.",
    "invalid_input": "Invalid receipt binding input.",
    "unsupported": "Receipt binding profile or representation is unsupported.",
    "resource_limit": "Receipt binding exceeds a declared resource bound.",
}
_REQUEST_KEYS = {
    "schema", "request_id", "profile", "kernel_commit", "editions", "context",
    "inquiry", "realisation_request_id", "realisation_result_id", "source_digest",
    "receipt_graph_id", "limits",
}
_ROLES = ("bundle", "result", "receipt")
_FIELD_DISPOSITION = {
    "Sigma": "reconstructed-adapter-signature",
    "B": "reconstructed-from-validated-joint-records",
    "G": "reconstructed-explicit-rule-list",
    "I": "reconstructed-adapter-interface",
    "A": "unresolved", "E": "unresolved", "D": "unresolved", "Pi": "unresolved",
    "K": "recomputed-with-semantic-limitations",
    "M": "reconstructed-edition-and-provenance",
    "place": "unresolved-independent-coordinates",
}


class ReceiptBindingError(ValueError):
    """A typed refusal with a fixed input-independent message."""

    def __init__(self, outcome: str = "invalid_input") -> None:
        if type(outcome) is not str or outcome not in {
            "invalid_input", "unsupported", "resource_limit",
        }:
            outcome = "invalid_input"
        self.outcome = outcome
        super().__init__(_MESSAGES[outcome])


def _require(condition: bool, outcome: str = "invalid_input") -> None:
    if not condition:
        raise ReceiptBindingError(outcome)


def _keys(value: Any, keys: set[str]) -> None:
    _require(type(value) is dict and len(value) == len(keys))
    _require(all(type(key) is str for key in value) and set(value) == keys)


def _identity(value: Any, *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    _require(type(value) is str and len(value) == 71 and bool(_DIGEST.fullmatch(value)))


def _text(value: Any, limit: int, *, outcome: str = "resource_limit") -> None:
    _require(type(value) is str and bool(value))
    _require(len(value) <= limit, outcome)
    try:
        size = len(value.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise ReceiptBindingError() from exc
    _require(size <= limit, outcome)


def _plain(value: Any, *, graph_budget: int | None = None) -> None:
    """Admit exact finite JSON containers before any canonical serialization.

    Graph-only ceilings never narrow the public upstream family/history profile.
    Active-path tracking permits shared subobjects but rejects actual cycles.
    Iterator frames avoid queuing all children before the next scalar's guard.
    """
    active: set[int] = set()
    stack = [(iter((value,)), -1, None)]
    nodes = 0
    text_bytes = 0
    while stack:
        iterator, parent_depth, container_id = stack[-1]
        try:
            item = next(iterator)
        except StopIteration:
            stack.pop()
            if container_id is not None:
                active.remove(container_id)
            continue
        depth = parent_depth + 1
        nodes += 1
        if graph_budget is not None:
            _require(depth <= 64 and nodes <= 200000, "resource_limit")
        kind = type(item)
        if item is None or kind is bool:
            continue
        if kind is str:
            if graph_budget is not None:
                _require(len(item) <= graph_budget, "resource_limit")
                try:
                    text_bytes += len(item.encode("utf-8"))
                except UnicodeEncodeError as exc:
                    raise ReceiptBindingError() from exc
                _require(text_bytes <= graph_budget, "resource_limit")
            continue
        if kind is int:
            if graph_budget is not None:
                _require(-(2 ** 127) <= item <= 2 ** 127, "resource_limit")
            continue
        if kind is float:
            _require(math.isfinite(item))
            continue
        _require(kind is dict or kind is list)
        _require(id(item) not in active)
        active.add(id(item))
        if kind is dict:
            # Keys are visited as values, so UTF-8 totals include every key.
            def children(record: dict[str, Any]):
                for key, child in record.items():
                    _require(type(key) is str)
                    yield key
                    yield child
            child_iterator = children(item)
        else:
            child_iterator = iter(item)
        stack.append((child_iterator, depth, id(item)))


def _same(actual: Any, expected: Any) -> None:
    # Python equality alone treats True == 1. Canonical comparison does not.
    _require(actual == expected)
    _require(canonical_bytes(actual) == canonical_bytes(expected))


def _raw_digest(raw: bytes) -> str:
    return "sha256:" + sha256(raw).hexdigest()


def _expected_editions() -> dict[str, str]:
    # Fresh literals keep mutable exported dictionaries from becoming policy.
    return {
        "family": "e7q.ir.candidate-family/v0alpha1",
        "history": "e7q.ir.transformation-history/v0alpha1",
        "realisation": "e7q.ir.realisation-result/v0alpha1",
        "rgp": "RGP2@v0.12.1-experimental",
    }


def _request_structure(request: Any, *, identified: bool) -> None:
    _keys(request, _REQUEST_KEYS if identified else _REQUEST_KEYS - {"request_id"})
    _require(type(request["schema"]) is str and request["schema"] == REQUEST_SCHEMA)
    for name in ("profile", "kernel_commit"):
        _text(request[name], 128)
    for name in ("context", "inquiry"):
        _text(request[name], 1024)
    _keys(request["editions"], set(_expected_editions()))
    for edition in request["editions"].values():
        _text(edition, 128)
    _keys(request["limits"], set(_CEILINGS))
    for name, ceiling in _CEILINGS.items():
        value = request["limits"][name]
        _require(type(value) is int and 1 <= value <= ceiling)
    for name in ("realisation_request_id", "realisation_result_id"):
        _identity(request[name])
    for name in ("source_digest", "receipt_graph_id"):
        _identity(request[name], nullable=True)
    if identified:
        _identity(request["request_id"])


def build_receipt_binding_request(
    *, realisation_request_id: str, realisation_result_id: str,
    context: str, inquiry: str, source_digest: str | None = None,
    receipt_graph_id: str | None = None, profile: str = PROFILE,
    kernel_commit: str = KERNEL_COMMIT, editions: dict[str, str] | None = None,
    max_graph_bytes: int = 16 * 1024 * 1024, max_artifacts: int = 64,
    max_relations: int = 128, max_source_bytes: int = 1048576,
) -> dict[str, Any]:
    """Build a structural request, without certifying any backing evidence."""
    request = {
        "schema": REQUEST_SCHEMA, "profile": profile, "kernel_commit": kernel_commit,
        "editions": _expected_editions() if editions is None else editions,
        "context": context, "inquiry": inquiry,
        "realisation_request_id": realisation_request_id,
        "realisation_result_id": realisation_result_id,
        "source_digest": source_digest, "receipt_graph_id": receipt_graph_id,
        "limits": {
            "max_graph_bytes": max_graph_bytes, "max_artifacts": max_artifacts,
            "max_relations": max_relations, "max_source_bytes": max_source_bytes,
        },
    }
    _request_structure(request, identified=False)
    request["editions"] = dict(request["editions"])
    request["request_id"] = identified_digest(request, "request_id")
    return request


def validate_receipt_binding_request(request: dict[str, Any]) -> None:
    """Validate exact built-in request fields and recompute the whole identity."""
    _request_structure(request, identified=True)
    _require(request["request_id"] == identified_digest(request, "request_id"))


def _result(outcome: str, bindings: dict[str, Any], *, best: list[str] | None = None,
            selected: str | None = None, evidence: dict[str, str] | None = None,
            layers: list[dict[str, Any]] | None = None,
            edges: list[dict[str, Any]] | None = None,
            witness: dict[str, Any] | None = None) -> dict[str, Any]:
    result = {
        "schema": RESULT_SCHEMA, "outcome": outcome, "request_id": None,
        "realisation_request_id": None, "realisation_result_id": None,
        "source_family_id": None, "history_id": None, "restriction_id": None,
        "input_residual_family_id": None, "realisation_outcome": None,
        "best_member_ids": [] if best is None else list(best),
        "selected_member_id": selected, "source_digest": None, "receipt_graph_id": None,
        "evidence_digests": evidence, "layer_records": [] if layers is None else layers,
        "edge_records": [] if edges is None else edges, "witness": witness,
        "message": _MESSAGES[outcome],
    }
    result.update(bindings)
    result["binding_id"] = identified_digest(result, "binding_id")
    return result


def _unknown() -> dict[str, Any]:
    return {"status": "unknown", "value": None}


def _declared(value: dict[str, Any]) -> dict[str, Any]:
    return {"status": "declared", "value": value}


def _layer(role: str, schema: str, refs: list[str], operations: list[str],
           rule: str | None = None) -> dict[str, Any]:
    layer = {
        "schema": LAYER_SCHEMA, "role": role, "state_refs": list(refs),
        "Sigma": _declared({"identity_scope": "product-local", "state_schema": schema}),
        "B": _declared({"record_refs": list(refs), "coupling": "joint-record-identity"}),
        "G": _declared({"rules": [] if rule is None else [{"id": rule, "edition": "1"}]}),
        "I": _declared({"state_schema": schema, "operations": list(operations),
                        "boundary": "offline record adapter; no execution"}),
        "A": _unknown(), "E": _unknown(), "D": _unknown(), "Pi": _unknown(),
        "K": {"status": "partial", "value": {
            "scope": "canonical-record-checks", "independently_recomputed": True,
            "semantic_preservation": "not-assessed", "execution_authentication": "not-assessed",
        }},
        "M": _declared({"kernel_commit": KERNEL_COMMIT, "adapter_edition": "1",
                        "role": role, "source_ids": list(refs)}),
        "place": {coordinate: _unknown() for coordinate in ("r", "rho", "tau", "alpha", "c")},
    }
    layer["layer_id"] = identified_digest(layer, "layer_id")
    return layer


def _edge(kind: str, origin: str, destination: str, rule: str, refs: list[str],
          parameters: dict[str, Any], variation: str, scope: str) -> dict[str, Any]:
    edge = {
        "schema": EDGE_SCHEMA, "kind": kind,
        "from_layer_id": origin, "to_layer_id": destination,
        "rule": {"id": rule, "edition": "1"}, "state_refs": list(refs),
        "parameters": parameters, "field_disposition": dict(_FIELD_DISPOSITION),
        "introduced_variation": variation,
        "unresolved": ["program-equivalence", "authenticated-execution",
                       "RGP-coordinates", "recursive-capacity"],
        "validation_scope": scope,
    }
    edge["edge_id"] = identified_digest(edge, "edge_id")
    return edge


def _bound(bindings: dict[str, Any], family: dict[str, Any], history: dict[str, Any],
           restriction: dict[str, Any], realised: dict[str, Any], selected: str,
           evidence: dict[str, str], openqasm_digest: str, target: str) -> dict[str, Any]:
    family_id = bindings["source_family_id"]
    history_id = bindings["history_id"]
    restriction_id = bindings["restriction_id"]
    residual_id = bindings["input_residual_family_id"]
    request_id = bindings["realisation_request_id"]
    result_id = bindings["realisation_result_id"]
    witness_id = realised["witness"]["witness_id"]
    step_id = history["steps"][0]["step_id"]
    graph_id = bindings["receipt_graph_id"]
    source_digest = bindings["source_digest"]
    layers = [
        _layer("source-family", _expected_editions()["family"], [family_id],
               ["restrict"], "qa4.restrict-metadata"),
        _layer("ordered-history", _expected_editions()["history"], [history_id, step_id],
               ["ordered-linkage"]),
        _layer("residual-family", "e7q.ir.candidate-restriction/v0alpha2",
               [restriction_id, residual_id], ["rank"], "qa4.rank-metadata"),
        _layer("realisation", _expected_editions()["realisation"],
               [request_id, result_id, witness_id], ["validate-selection"]),
        _layer("supplied-receipt", "e7q.ir.graph/v0alpha1",
               [graph_id, evidence["bundle"], evidence["result"], evidence["receipt"]],
               ["recover-supplied-bytes", "validate-internal-consistency"]),
    ]
    layer_ids = [layer["layer_id"] for layer in layers]
    edges = [
        _edge("generates-metadata", layer_ids[0], layer_ids[2], "qa4.restrict-metadata",
              [history_id, step_id, restriction_id],
              {"family_id": family_id, "history_id": history_id, "step_id": step_id,
               "restriction_id": restriction_id,
               "retained_member_ids": list(restriction["retained_member_ids"])},
              "restricted-member-inventory", "recomputed-restriction"),
        _edge("generates-metadata", layer_ids[2], layer_ids[3], "qa4.rank-metadata",
              [request_id, result_id, witness_id],
              {"residual_family_id": residual_id, "request_id": request_id,
               "result_id": result_id, "witness_id": witness_id},
              "ranked-best-inventory", "recomputed-integer-ranking"),
        _edge("references-evidence", layer_ids[3], layer_ids[4], "qa4.link-supplied-bytes",
              [selected, graph_id],
              {"selected_member_id": selected, "graph_id": graph_id,
               "source_digest": source_digest, "bundle_digest": evidence["bundle"],
               "result_digest": evidence["result"], "receipt_digest": evidence["receipt"],
               "openqasm_digest": openqasm_digest, "target": target},
              "supplied-evidence-reference", "supplied-byte-and-target-linkage"),
    ]
    witness = {
        "schema": WITNESS_SCHEMA, "realisation_witness_id": witness_id,
        "selected_member_id": selected, "source_digest": source_digest,
        "receipt_graph_id": graph_id, "evidence_digests": dict(evidence),
        "openqasm_digest": openqasm_digest, "target": target,
        "layer_ids": layer_ids, "edge_ids": [edge["edge_id"] for edge in edges],
    }
    witness["witness_id"] = identified_digest(witness, "witness_id")
    return _result("bound", bindings, best=[selected], selected=selected,
                   evidence=dict(evidence), layers=layers, edges=edges, witness=witness)


def _pass_report(report: Any, *, legacy: bool = False) -> None:
    _require(type(report) is dict and type(report.get("status")) is str
             and report["status"] == "PASS")
    if legacy:
        _keys(report, {"status", "reason", "checks"})
        _require(type(report["reason"]) is str and bool(report["reason"]))
    checks = report.get("checks")
    _require(type(checks) is list and bool(checks))
    for check in checks:
        _require(type(check) is dict and check.get("passed") is True)
        if legacy:
            _keys(check, {"name", "passed", "message"})
            for field in ("name", "message"):
                _require(type(check[field]) is str and bool(check[field]))


def assess_receipt_binding(
    request: dict[str, Any], family: dict[str, Any], history: dict[str, Any],
    realisation_request: dict[str, Any], realisation_result: dict[str, Any],
    restriction: dict[str, Any] | None = None, *, source_bytes: bytes | None = None,
    receipt_graph: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Replay planning selection, then recover and validate supplied evidence.

    Carrier length checks precede public evidence parsing. Public recovery still
    performs its independently bounded base64 decoding before returning bytes.
    """
    bindings: dict[str, Any] = {}
    try:
        validate_receipt_binding_request(request)
        bindings["request_id"] = request["request_id"]
        _require(request["profile"] == PROFILE and request["kernel_commit"] == KERNEL_COMMIT
                 and request["editions"] == _expected_editions(), "unsupported")
        # No extra backing-family size/string caps: public Q-A3 retains authority.
        for record in (family, history, realisation_request, realisation_result, restriction):
            _plain(record)
        validate_realisation_request(realisation_request)
        realised = assess_realisation(realisation_request, family, history, restriction)
        validate_realisation_result(realisation_result, realisation_request, family, history, restriction)
        _same(realisation_result, realised)
        _require(request["realisation_request_id"] == realisation_request["request_id"]
                 and request["realisation_result_id"] == realised["result_id"])
        _require(request["context"] == realisation_request["context"]
                 and request["inquiry"] == realisation_request["inquiry"])
        _require(type(family) is dict and type(history) is dict)
        _require(realisation_request["source_family_id"] == family.get("family_id")
                 and realisation_request["history_id"] == history.get("history_id")
                 and request["context"] == history.get("context")
                 and request["inquiry"] == history.get("inquiry"))
        bindings.update(
            realisation_request_id=realisation_request["request_id"],
            realisation_result_id=realised["result_id"],
            source_family_id=realised["source_family_id"], history_id=realised["history_id"],
            restriction_id=realised["restriction_id"],
            input_residual_family_id=realised["input_residual_family_id"],
            realisation_outcome=realised["outcome"],
        )
        if realised["outcome"] != "unique":
            _require(request["source_digest"] is None and request["receipt_graph_id"] is None
                     and source_bytes is None and receipt_graph is None)
            return _result("unbound", bindings,
                           best=realised["best_member_ids"] if realised["outcome"] == "ambiguous" else [])
        _require(type(source_bytes) is bytes and type(receipt_graph) is dict)
        _identity(request["source_digest"])
        _identity(request["receipt_graph_id"])
        limits = request["limits"]
        _require(len(source_bytes) <= limits["max_source_bytes"], "resource_limit")
        source_digest = _raw_digest(source_bytes)
        _identity(receipt_graph.get("graph_id"))
        _require(request["source_digest"] == source_digest
                 and request["receipt_graph_id"] == receipt_graph["graph_id"])
        bindings.update(source_digest=source_digest, receipt_graph_id=receipt_graph["graph_id"])
        _plain(receipt_graph, graph_budget=limits["max_graph_bytes"])
        for field, limit in (("artifacts", "max_artifacts"), ("relations", "max_relations")):
            _require(type(receipt_graph.get(field)) is list)
            _require(len(receipt_graph[field]) <= limits[limit], "resource_limit")
        _require(len(canonical_bytes(receipt_graph)) <= limits["max_graph_bytes"], "resource_limit")
        selected = realised["selected_member_id"]
        _require(restriction is not None and selected in restriction["retained_member_ids"])
        _require(selected in restriction["result_family"]["member_ids"])
        members = [member for member in family["members"] if member["member_id"] == selected]
        _require(len(members) == 1)
        commitments = members[0]["bindings"]
        reserved = {"qa4_source_digest", "qa4_bundle_digest", "qa4_openqasm_digest", "qa4_target"}
        _require(reserved <= set(commitments), "unsupported")
        for key in ("qa4_source_digest", "qa4_bundle_digest", "qa4_openqasm_digest"):
            _identity(commitments[key])
        _text(commitments["qa4_target"], 128, outcome="invalid_input")
        _require(commitments["qa4_source_digest"] == source_digest == family["source_id"])
        _pass_report(validate_graph(receipt_graph, level="F1"))
        extensions = receipt_graph.get("extensions")
        _require(type(extensions) is dict)
        dialect = extensions.get("workflow_format")
        _require(type(dialect) is str and bool(dialect))
        _require(dialect == WORKFLOW_FORMAT, "unsupported")
        refs = extensions.get("source_refs")
        _keys(refs, set(_ROLES))
        for ref in refs.values():
            _require(type(ref) is str and bool(ref))
        _require(len(set(refs.values())) == 3)
        raw = {}
        for role in _ROLES:
            matches = [artifact for artifact in receipt_graph["artifacts"]
                       if artifact["kind"] == "source"
                       and artifact["payload"].get("adapter") == SOURCE_ADAPTER
                       and artifact["payload"].get("role") == role]
            _require(len(matches) == 1
                     and matches[0]["payload"].get("stable_source_ref") == refs[role])
            carrier = recover_legacy_source(receipt_graph, refs[role])
            _require(type(carrier) is bytes)
            _require(len(carrier) <= limits["max_source_bytes"], "resource_limit")
            raw[role] = carrier
        _pass_report(validate_legacy_receipt_evidence(receipt_graph), legacy=True)
        parsed = {role: json.loads(raw[role].decode("utf-8")) for role in _ROLES}
        _require(all(type(value) is dict for value in parsed.values()))
        bundle = parsed["bundle"]
        evidence = {role: _raw_digest(raw[role]) for role in _ROLES}
        _require(type(bundle.get("openqasm")) is str)
        openqasm_digest = _raw_digest(bundle["openqasm"].encode("utf-8"))
        target = bundle.get("target")
        _text(target, 128, outcome="invalid_input")
        _require(commitments["qa4_bundle_digest"] == evidence["bundle"])
        _require(commitments["qa4_openqasm_digest"] == openqasm_digest == bundle.get("openqasm_digest"))
        _require(commitments["qa4_source_digest"] == bundle.get("source_digest"))
        _require(commitments["qa4_target"] == target == parsed["result"].get("target")
                 == parsed["receipt"].get("target"))
        return _bound(bindings, family, history, restriction, realised, selected,
                      evidence, openqasm_digest, target)
    except ReceiptBindingError as exc:
        return _result(exc.outcome, bindings)
    except (RealisationError, KeyError, TypeError, ValueError, UnicodeError, RecursionError, OverflowError):
        return _result("invalid_input", bindings)


def validate_receipt_binding_result(
    result: dict[str, Any], request: dict[str, Any], family: dict[str, Any],
    history: dict[str, Any], realisation_request: dict[str, Any],
    realisation_result: dict[str, Any], restriction: dict[str, Any] | None = None,
    *, source_bytes: bytes | None = None, receipt_graph: dict[str, Any] | None = None,
) -> None:
    """Recompute the entire assessment; rehashing a forged wrapper cannot pass."""
    try:
        _plain(result)
        expected = assess_receipt_binding(
            request, family, history, realisation_request, realisation_result, restriction,
            source_bytes=source_bytes, receipt_graph=receipt_graph,
        )
        _same(result, expected)
    except ReceiptBindingError:
        raise
    except (KeyError, TypeError, ValueError, UnicodeError, RecursionError, OverflowError) as exc:
        raise ReceiptBindingError() from exc
