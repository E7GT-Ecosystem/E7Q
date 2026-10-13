# SPDX-License-Identifier: Apache-2.0
"""Conservative allocation preflight, not a hard process sandbox or OOM oracle."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from .language import E7QError, E7QResourceLimitError, Program

DEFAULT_MEMORY_BUDGET_BYTES = 256 * 1024**2
RUNTIME_ALLOWANCE_BYTES = 64 * 1024**2


@dataclass(frozen=True)
class ExecutionPolicy:
    memory_budget_bytes: int = DEFAULT_MEMORY_BUDGET_BYTES
    respect_host_limits: bool = True

    def __post_init__(self) -> None:
        if type(self.memory_budget_bytes) is not int or self.memory_budget_bytes < 1:
            raise ValueError("memory_budget_bytes must be a positive integer")
        if type(self.respect_host_limits) is not bool:
            raise ValueError("respect_host_limits must be boolean")


class ResourceBlocked(E7QResourceLimitError):
    def __init__(self, assessment: dict[str, object]):
        self.assessment = assessment
        super().__init__("execution blocked before allocation: " + str(assessment["reason"]))


class AllocationFailed(E7QError):
    """A catchable allocation failure, not confirmation of a host OOM kill."""

    def __init__(self, scope: str, backend: str):
        self.assessment = {
            "schema": "e7q.execution-outcome/1", "status": "FAILED",
            "execution_status": "FAILED", "verification_status": "NOT_ASSESSED",
            "reason": "catchable-allocation-failure", "scope": scope,
            "backend": backend, "confirmed_oom": False,
        }
        super().__init__("catchable allocation failure during " + scope)


def failure_result(exc: ResourceBlocked | AllocationFailed) -> dict[str, object]:
    return {
        "schema": "e7q.execution-outcome/1",
        "status": "RESOURCE_BLOCKED" if isinstance(exc, ResourceBlocked) else "FAILED",
        "execution_status": "RESOURCE_BLOCKED" if isinstance(exc, ResourceBlocked) else "FAILED",
        "verification_status": "NOT_ASSESSED", "checks": [],
        "detail": exc.assessment,
        "boundary": "Structural admission is separate; no execution/property success is established.",
    }


def validate_program(program: Program) -> None:
    """Guard direct Program callers as well as parsed sources before allocating."""
    for name, maximum in (("qubits", 4096), ("bits", 4096), ("shots", 1_000_000)):
        value = getattr(program, name)
        if type(value) is not int or not 1 <= value <= maximum:
            raise E7QError(f"execution {name} must be in 1..{maximum}")
    if len(program.operations) > 100_000:
        raise E7QError("execution exceeds 100000 operations")
    if program.backend not in {"statevector", "densitymatrix", "stabilizer"}:
        raise E7QError("unsupported execution backend")
    for operation in program.operations:
        if any(type(q) is not int or not 0 <= q < program.qubits for q in operation.qubits):
            raise E7QError("execution qubit index out of range")
        if any(type(b) is not int or not 0 <= b < program.bits for b in operation.bits):
            raise E7QError("execution bit index out of range")
        if operation.condition is not None:
            bit, value = operation.condition
            if type(bit) is not int or not 0 <= bit < program.bits or value not in (0, 1):
                raise E7QError("invalid execution condition")
        if operation.gate in {"X", "Y", "Z", "H", "S", "T"}:
            if len(operation.qubits) != 1:
                raise E7QError("one-qubit gate requires one operand")
        elif operation.gate in {"CX", "CZ", "SWAP"}:
            if len(operation.qubits) != 2 or operation.qubits[0] == operation.qubits[1]:
                raise E7QError("two-qubit gate requires distinct operands")
        elif operation.gate == "MEASURE":
            if operation.full_register:
                if program.bits < program.qubits:
                    raise E7QError("full measurement requires bits >= qubits")
            elif len(operation.qubits) != 1 or len(operation.bits) != 1:
                raise E7QError("individual measurement requires one qubit and one bit")
        elif operation.gate == "ASSERT":
            if operation.condition is None:
                raise E7QError("assertion requires a condition")
        elif operation.gate == "NOISE":
            if (len(operation.qubits) != 1 or operation.label not in
                    {"bit_flip", "phase_flip", "depolarizing"} or
                    operation.probability is None or not 0 <= operation.probability <= 1):
                raise E7QError("invalid noise operation")
        else:
            raise E7QError(f"unsupported operation: {operation.gate}")
        if operation.gate == "MEASURE" and operation.condition is not None:
            raise E7QError("conditional measurement is unsupported")
    if program.backend == "densitymatrix":
        if any(op.condition is not None or op.gate == "ASSERT" or
               (op.gate == "MEASURE" and not op.full_register) for op in program.operations):
            raise E7QError("densitymatrix requires terminal full-register measurement")
    elif program.backend == "statevector" and any(op.gate == "NOISE" for op in program.operations):
        raise E7QError("noise requires densitymatrix backend")


def host_headroom() -> list[dict[str, object]]:
    """Best-effort Linux v2 ancestor limits and POSIX address-space headroom.

    Unavailable/ambiguous signals are omitted, never reported as enforced limits.
    Half of detected headroom is usable to leave room for other activity.
    """
    limits: list[dict[str, object]] = []
    try:
        fields = {line.split(':')[0]: line.split(':')[1].strip()
                  for line in Path('/proc/meminfo').read_text().splitlines()}
        available = int(fields['MemAvailable'].split()[0]) * 1024
        limits.append({"source": "linux-MemAvailable", "headroom_bytes": available})
    except (OSError, ValueError, KeyError):
        pass
    try:
        membership = next(line[3:] for line in Path('/proc/self/cgroup').read_text().splitlines()
                          if line.startswith('0::'))
        root = Path('/sys/fs/cgroup').resolve()
        current = (root / membership.lstrip('/')).resolve()
        if current.is_relative_to(root):
            while current.is_relative_to(root):
                maximum = (current / 'memory.max').read_text().strip()
                used = int((current / 'memory.current').read_text().strip())
                if maximum != 'max':
                    limits.append({"source": "linux-cgroup-v2:" + str(current),
                                   "headroom_bytes": max(0, int(maximum) - used)})
                if current == root:
                    break
                current = current.parent
    except (OSError, ValueError, StopIteration):
        pass
    try:
        import resource
        soft, _ = resource.getrlimit(resource.RLIMIT_AS)
        if soft != resource.RLIM_INFINITY:
            virtual = int(Path('/proc/self/statm').read_text().split()[0]) * os.sysconf('SC_PAGE_SIZE')
            limits.append({"source": "posix-RLIMIT_AS-headroom", "headroom_bytes": max(0, soft - virtual)})
    except (ImportError, AttributeError, OSError, ValueError):
        pass
    return limits


def preflight(program: Program, policy: ExecutionPolicy | None = None,
              *, representation: str | None = None) -> dict[str, object]:
    validate_program(program)
    policy = policy or ExecutionPolicy()
    limits = host_headroom() if policy.respect_host_limits else []
    usable = min([policy.memory_budget_bytes] + [int(x['headroom_bytes']) // 2 for x in limits])
    kind = representation or program.backend
    if kind not in {"statevector", "densitymatrix", "stabilizer", "unitary", "superoperator"}:
        raise E7QError("unsupported allocating representation")
    if representation is None and not any(op.gate == "MEASURE" for op in program.operations):
        raise E7QError("execution requires measurement")
    n = program.qubits
    dynamic = any(op.condition is not None or (op.gate == 'MEASURE' and not op.full_register)
                  for op in program.operations)
    # Python dictionaries and serialized strings dominate sparse-output worst cases.
    outcome_count = min(program.shots, 1 << min(program.bits, 30)) if dynamic or kind == 'stabilizer' else 1 << min(n, 30)
    output = outcome_count * (768 + 4 * program.bits) + len(program.operations) * 2048
    too_wide = kind != 'stabilizer' and n > 30
    if too_wide:
        storage = None
        working = None
    elif kind == 'stabilizer':
        storage = 8 * n * n + 256 * n
        working = RUNTIME_ALLOWANCE_BYTES + 4 * storage + output
    else:
        exponent = n if kind == 'statevector' else (4 * n if kind == 'superoperator' else 2 * n)
        storage = 16 * (1 << exponent)
        # Includes live/final/prepared states, bounded gate/collapse temporaries,
        # probability work, matrices/columns for explicit equivalence outputs.
        multiplier = 12 if kind in {'superoperator', 'unitary'} else 8
        working = RUNTIME_ALLOWANCE_BYTES + multiplier * storage + output
    reason = ('dense widths above 30 are refused without exponent-sized allocation'
              if too_wide else f'estimated working bytes {working} exceed usable budget {usable}')
    assessment: dict[str, object] = {
        'schema': 'e7q.resource-preflight/1', 'backend': program.backend,
        'representation': kind, 'dtype': 'compact-tableau' if kind == 'stabilizer' else 'complex128',
        'state_storage_bytes': storage, 'estimated_working_bytes': working,
        'output_allowance_bytes': output, 'runtime_allowance_bytes': RUNTIME_ALLOWANCE_BYTES,
        'configured_budget_bytes': policy.memory_budget_bytes, 'usable_budget_bytes': usable,
        'host_headroom': limits, 'host_fraction': 0.5, 'host_limits_respected': policy.respect_host_limits,
        'estimate_not_measured_rss': True, 'enforced_process_limit': False,
        'status': 'RESOURCE_BLOCKED' if too_wide or working > usable else 'ADMITTED',
        'reason': reason if too_wide or working > usable else 'conservative estimate within budget',
    }
    if assessment['status'] != 'ADMITTED':
        raise ResourceBlocked(assessment)
    return assessment
