# SPDX-License-Identifier: Apache-2.0
"""Independent QA4-PACKAGE/2026-10-14/1 supplied-byte contract probes.

Authored against package SHA256 065d43e1c4434d9c50f6c9630d54f08ec17829898c4177288f23047c9c0f21df,
without reading receipt_binding.py. Carriers are handwritten inert JSON, never
compiler/bundle-builder/simulator/native/provider/CLI fixtures. The only writes
at test time are supplied carriers in this suite's own pytest temporary paths.
"""
import copy
from hashlib import sha256
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from e7q.ir import receipt_binding as binding
from e7q.ir import legacy_receipt_workflow as workflow
from e7q.ir.candidate_family import (
    assess_candidate_restriction, build_candidate_family, factor,
    validate_candidate_family,
)
from e7q.ir.canonical import canonical_bytes, identified_digest
from e7q.ir.conformance import validate_graph
from e7q.ir.graph import RELATION_KINDS, build_graph
from e7q.ir.realisation import (
    assess_realisation, build_realisation_request, validate_realisation_result,
)
from e7q.ir.transformation_history import (
    build_transformation_history, transformation_step,
)


FOREIGN = "sha256:" + "f" * 64
KERNEL = "fc4cdf95c6434e653efbe017587aab60b4b2a86c"
EDITIONS = {
    "family": "e7q.ir.candidate-family/v0alpha1",
    "history": "e7q.ir.transformation-history/v0alpha1",
    "realisation": "e7q.ir.realisation-result/v0alpha1",
    "rgp": "RGP2@v0.12.1-experimental",
}
SCHEMA = Path(__file__).resolve().parents[1] / "schemas/e7q-ir-receipt-binding-v0alpha1.schema.json"
MESSAGES = {
    "bound": "Selected member is linked to supplied internally consistent receipt evidence.",
    "unbound": "No unique member is available for receipt binding.",
    "invalid_input": "Invalid receipt binding input.",
    "unsupported": "Receipt binding profile or representation is unsupported.",
    "resource_limit": "Receipt binding exceeds a declared resource bound.",
}
UNKNOWN = {"status": "unknown", "value": None}
COMPONENTS = ["Sigma", "B", "G", "I", "A", "E", "D", "Pi", "K", "M"]
DISPOSITIONS = {
    "Sigma": "reconstructed-adapter-signature",
    "B": "reconstructed-from-validated-joint-records",
    "G": "reconstructed-explicit-rule-list",
    "I": "reconstructed-adapter-interface",
    "A": "unresolved", "E": "unresolved", "D": "unresolved", "Pi": "unresolved",
    "K": "recomputed-with-semantic-limitations",
    "M": "reconstructed-edition-and-provenance",
    "place": "unresolved-independent-coordinates",
}
UNRESOLVED = ["program-equivalence", "authenticated-execution", "RGP-coordinates", "recursive-capacity"]
RESULT_KEYS = {
    "schema", "binding_id", "outcome", "request_id", "realisation_request_id",
    "realisation_result_id", "source_family_id", "history_id", "restriction_id",
    "input_residual_family_id", "realisation_outcome", "best_member_ids",
    "selected_member_id", "source_digest", "receipt_graph_id", "evidence_digests",
    "layer_records", "edge_records", "witness", "message",
}
REQUEST_KEYS = {
    "schema", "request_id", "profile", "kernel_commit", "editions", "context",
    "inquiry", "realisation_request_id", "realisation_result_id", "source_digest",
    "receipt_graph_id", "limits",
}


def raw_digest(raw):
    return "sha256:" + sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def rehash(record, field):
    record[field] = identified_digest(record, field)
    return record


def inert_carriers(source=b"inert source bytes\n", target="inert-target", shots=4,
                   openqasm="OPENQASM 2.0; // inert supplied text\n", spaced=False):
    """Calculate the old receipt contract in memory, without its builder."""
    bundle = {
        "schema": "e7q.execution-bundle/v1", "status": "READY", "submitted": False,
        "target": target, "shots": shots, "source_digest": raw_digest(source),
        "openqasm": openqasm, "openqasm_digest": raw_digest(openqasm.encode("utf-8")),
        "planning": {"compiled": {"inert": "not compiled or executed", "proof": [{"step": 0}]}},
        "proof": [{"step": 0, "kind": "inert supplied bundle"}],
    }
    bundle_raw = (json.dumps(bundle, indent=1, ensure_ascii=False).encode("utf-8") + b"\n") if spaced else encoded(bundle)
    result = {
        "schema": "e7q.execution-result/v1", "provider": "inert-provider",
        "job_id": "inert-job", "target": target, "shots": shots,
        "counts": {"0": shots}, "completed_at": "supplied-inert-time",
        "bundle_digest": raw_digest(bundle_raw),
    }
    result_raw = encoded(result)
    receipt = {
        "schema": "e7q.execution-receipt/v1", "status": "PASS",
        "bundle_digest": raw_digest(bundle_raw), "result_digest": raw_digest(result_raw),
        "provider": result["provider"], "job_id": result["job_id"], "target": target,
        "shots": shots, "completed_at": result["completed_at"],
        "counts": {"0": shots}, "probabilities": {"0": 1.0},
        "proof": [
            {"step": 0, "kind": "bundle-linkage", "bundle_digest": raw_digest(bundle_raw),
             "source_digest": bundle["source_digest"], "openqasm_digest": bundle["openqasm_digest"]},
            {"step": 1, "kind": "supplied-result", "result_digest": raw_digest(result_raw),
             "provider": result["provider"], "job_id": result["job_id"], "completed_at": result["completed_at"]},
            {"step": 2, "kind": "result-validation", "target": target, "shots": shots,
             "count_total": shots, "status": "PASS"},
            {"step": 3, "kind": "evidence-boundary", "boundary":
             "Receipt validates internal consistency and bundle linkage of user-supplied data. E7Q did not authenticate the provider, submit or witness the job, or establish physical fidelity."},
        ],
        "temporal_evidence": {
            "schema": "e7q.temporal-evidence/v2", "temporal_order_roles": ["TD0"],
            "carrier_ref": raw_digest(bundle_raw),
            "carrier_description": "one provider-reported execution-result event",
            "order_relation": "single reported completion point",
            "chronology_status": "provider-reported-not-authenticated",
            "projection": {
                "from": "user-supplied provider result", "to": "normalized E7Q execution receipt",
                "preserves": ["reported completion time", "bundle and result linkage", "counts and empirical probabilities"],
                "loses": ["shot-level ordering and timing", "intermediate quantum states", "provider-authenticated chronology"],
            },
            "reconstruction": {"status": "non-unique", "limit":
                               "Multiple shot sequences and device histories can produce the same aggregate counts."},
            "clock": {"field": "completed_at", "value": result["completed_at"], "status": "provider-reported-not-authenticated"},
            "temporal_phase": {"criterion_id": "e7q.receipt-consistency", "criterion_edition": "1",
                               "parameters": {}, "description": "bundle linkage and count consistency", "status": "PASS"},
            "boundary_crossing": {"detected": False},
        },
    }
    return {"bundle": bundle_raw, "result": result_raw, "receipt": encoded(receipt)}


def mapped_graph(tmp_path, raw):
    paths = []
    for role in ("bundle", "result", "receipt"):
        path = tmp_path / (role + ".json")
        path.write_bytes(raw[role])
        paths.append(path)
    return workflow.build_legacy_receipt_graph(
        *paths, count_label_order="clbit-ascending", created_at="2026-10-14T00:00:00Z",
        bundle_source_ref="inert:bundle", result_source_ref="inert:result",
        receipt_source_ref="inert:receipt", name="Q-A4 inert offline evidence",
    )


def commitment_bindings(raw, source):
    bundle = json.loads(raw["bundle"])
    return {
        "qa4_source_digest": raw_digest(source), "qa4_bundle_digest": raw_digest(raw["bundle"]),
        "qa4_openqasm_digest": raw_digest(bundle["openqasm"].encode("utf-8")),
        "qa4_target": bundle["target"],
    }


def planning_case(case, *, alternatives=None, keep="all", vectors=None,
                  terminal=None, objectives=None, assumptions=(), limitations=()):
    """Rebuild an explicit new input claim through unchanged public Q-A1--3."""
    bridges = commitment_bindings(case["raw"], case["source"])
    alternatives = alternatives if alternatives is not None else [dict(bridges, label=label) for label in ("a", "b", "c")]
    family = build_candidate_family(raw_digest(case["source"]), [factor("joint", list(alternatives[0]), alternatives)],
                                    assumptions=assumptions, limitations=limitations)
    members = [member["member_id"] for member in family["members"]]
    retained = members if keep == "all" else members[:2] if keep == "partial" else []
    if terminal:
        restriction = None
        step = transformation_step(index=0, kind="restrict", rule_id="inert-domain", rule_edition="1",
                                   input_family_id=family["family_id"], admitted_member_ids=members,
                                   outcome=terminal, message="Inert terminal declaration.")
    else:
        restriction = assess_candidate_restriction(family, retained, criterion_id="inert-domain",
                                                    criterion_edition="1", criterion_text="Explicit inert inventory")
        step = transformation_step(index=0, kind="restrict", rule_id="inert-domain", rule_edition="1",
                                   input_family_id=family["family_id"], admitted_member_ids=restriction["retained_member_ids"],
                                   excluded_member_ids=restriction["excluded_member_ids"], outcome=restriction["outcome"],
                                   output_family_id=restriction["result_family"]["family_id"] if restriction["result_family"] else None,
                                   message=restriction["message"])
    history = build_transformation_history(family["family_id"], [step], context="inert planning", inquiry="supplied byte linkage")
    objectives = objectives or [{"id": "cost", "edition": "1", "direction": "min", "unit": "inert"}]
    vectors = vectors if vectors is not None else [(index,) for index in range(len(retained))]
    rows = [] if terminal else [
        {"member_id": member, "values": [{"objective_id": objective["id"], "value": value, "evidence_ref": FOREIGN}
                                           for objective, value in zip(objectives, vector)]}
        for member, vector in zip(retained, vectors)
    ]
    rr = build_realisation_request(source_family_id=family["family_id"], history_id=history["history_id"],
                                   restriction_id=restriction["restriction_id"] if restriction else None,
                                   input_residual_family_id=history["residual_family_id"], objectives=objectives,
                                   objective_rows=rows, context=history["context"], inquiry=history["inquiry"])
    rz = assess_realisation(rr, family, history, restriction)
    validate_realisation_result(rz, rr, family, history, restriction)
    case.update(family=family, history=history, restriction=restriction, rr=rr, rz=rz)
    request_for(case, evidence=rz["outcome"] == "unique")
    return case


def request_for(case, *, evidence=True, **overrides):
    kwargs = dict(realisation_request_id=case["rr"]["request_id"], realisation_result_id=case["rz"]["result_id"],
                  context=case["history"]["context"], inquiry=case["history"]["inquiry"],
                  source_digest=raw_digest(case["source"]) if evidence else None,
                  receipt_graph_id=case["graph"]["graph_id"] if evidence else None)
    kwargs.update(overrides)
    case["request"] = binding.build_receipt_binding_request(**kwargs)
    return case["request"]


def assess(case, *, evidence=None):
    evidence = case["rz"]["outcome"] == "unique" if evidence is None else evidence
    return binding.assess_receipt_binding(case["request"], case["family"], case["history"], case["rr"], case["rz"],
                                           case["restriction"], source_bytes=case["source"] if evidence else None,
                                           receipt_graph=case["graph"] if evidence else None)


def validate_result(result, case, *, evidence=None):
    evidence = case["rz"]["outcome"] == "unique" if evidence is None else evidence
    return binding.validate_receipt_binding_result(result, case["request"], case["family"], case["history"],
                                                    case["rr"], case["rz"], case["restriction"],
                                                    source_bytes=case["source"] if evidence else None,
                                                    receipt_graph=case["graph"] if evidence else None)


def error(outcome, function, *args, **kwargs):
    with pytest.raises(binding.ReceiptBindingError) as caught:
        function(*args, **kwargs)
    assert caught.value.outcome == outcome
    assert str(caught.value) == MESSAGES[outcome]


def assert_outcome(result, outcome):
    assert set(result) == RESULT_KEYS
    assert result["schema"] == "e7q.ir.receipt-binding-result/v0alpha1"
    assert result["outcome"] == outcome
    assert result["message"] == MESSAGES[outcome]
    assert result["binding_id"] == identified_digest(result, "binding_id")
    if outcome != "bound":
        assert result["selected_member_id"] is None
        assert result["evidence_digests"] is None
        assert result["witness"] is None
        assert result["layer_records"] == result["edge_records"] == []
    if outcome not in {"bound", "unbound"}:
        assert result["best_member_ids"] == []


def no_evidence(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Evidence access occurred before its admission gate")
    # Only documented public calls, not private helpers, are intercepted.
    for name in ("validate_graph", "recover_legacy_source", "validate_legacy_receipt_evidence"):
        monkeypatch.setattr(binding, name, forbidden)


@pytest.fixture
def case(tmp_path):
    source = b"inert source bytes\n"
    raw = inert_carriers(source)
    graph = mapped_graph(tmp_path, raw)
    assert validate_graph(graph, level="F1")["status"] == "PASS"
    report = workflow.validate_legacy_receipt_evidence(graph)
    assert report["status"] == "PASS"
    assert all(check["passed"] is True for check in report["checks"])
    return planning_case(dict(source=source, raw=raw, graph=graph))


@pytest.fixture(scope="module")
def schema_validator():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def test_public_constants_request_identity_and_nonmutation(case, schema_validator):
    assert binding.PROFILE == "e7q.ir.selected-legacy-receipt-binding/v0alpha1"
    assert binding.KERNEL_COMMIT == KERNEL
    assert binding.EDITIONS == EDITIONS
    for name, suffix in [("REQUEST_SCHEMA", "request"), ("RESULT_SCHEMA", "result"),
                         ("LAYER_SCHEMA", "layer"), ("EDGE_SCHEMA", "edge"), ("WITNESS_SCHEMA", "witness")]:
        assert getattr(binding, name) == "e7q.ir.receipt-binding-" + suffix + "/v0alpha1"
    request = case["request"]
    assert set(request) == REQUEST_KEYS
    assert request["limits"] == {"max_graph_bytes": 16 * 1024 * 1024, "max_artifacts": 64,
                                  "max_relations": 128, "max_source_bytes": 1048576}
    assert request["editions"] == EDITIONS
    assert request["request_id"] == identified_digest(request, "request_id")
    before = copy.deepcopy(case)
    assert binding.validate_receipt_binding_request(request) is None
    schema_validator.validate(request)
    result = assess(case)
    assert_outcome(result, "bound")
    schema_validator.validate(result)
    assert validate_result(result, case) is None
    assert assess(case) == result
    assert case == before


def test_exact_five_layers_ten_components_five_places_three_edges_and_witness(case, schema_validator):
    result = assess(case)
    assert_outcome(result, "bound")
    family, history, restriction, rr, rz, graph = [case[key] for key in ("family", "history", "restriction", "rr", "rz", "graph")]
    digests = {role: raw_digest(raw) for role, raw in case["raw"].items()}
    selected = rz["selected_member_id"]
    step = history["steps"][0]
    assert result["best_member_ids"] == [selected]
    assert result["selected_member_id"] == selected
    assert result["evidence_digests"] == digests
    assert result["realisation_outcome"] == "unique"
    assert result["request_id"] == case["request"]["request_id"]
    for key, value in {"realisation_request_id": rr["request_id"], "realisation_result_id": rz["result_id"],
                       "source_family_id": family["family_id"], "history_id": history["history_id"],
                       "restriction_id": restriction["restriction_id"], "input_residual_family_id": history["residual_family_id"],
                       "source_digest": raw_digest(case["source"]), "receipt_graph_id": graph["graph_id"]}.items():
        assert result[key] == value
    roles = ["source-family", "ordered-history", "residual-family", "realisation", "supplied-receipt"]
    schemas = [EDITIONS["family"], EDITIONS["history"], "e7q.ir.candidate-restriction/v0alpha2", EDITIONS["realisation"], "e7q.ir.graph/v0alpha1"]
    refs = [[family["family_id"]], [history["history_id"], step["step_id"]],
            [restriction["restriction_id"], history["residual_family_id"]],
            [rr["request_id"], rz["result_id"], rz["witness"]["witness_id"]],
            [graph["graph_id"], digests["bundle"], digests["result"], digests["receipt"]]]
    operations = [["restrict"], ["ordered-linkage"], ["rank"], ["validate-selection"],
                  ["recover-supplied-bytes", "validate-internal-consistency"]]
    rules = [[{"id": "qa4.restrict-metadata", "edition": "1"}], [], [{"id": "qa4.rank-metadata", "edition": "1"}], [], []]
    layers = result["layer_records"]
    assert len(layers) == 5
    for index, layer in enumerate(layers):
        assert set(layer) == {"schema", "layer_id", "role", "state_refs", "place", *COMPONENTS}
        assert layer["schema"] == "e7q.ir.receipt-binding-layer/v0alpha1"
        assert layer["layer_id"] == identified_digest(layer, "layer_id")
        assert layer["role"] == roles[index]
        assert layer["state_refs"] == refs[index]
        for name in ("Sigma", "B", "G", "I", "M"):
            assert set(layer[name]) == {"status", "value"}
            assert layer[name]["status"] == "declared"
        assert layer["Sigma"]["value"] == {"identity_scope": "product-local", "state_schema": schemas[index]}
        assert layer["B"]["value"] == {"record_refs": refs[index], "coupling": "joint-record-identity"}
        assert layer["G"]["value"] == {"rules": rules[index]}
        assert layer["I"]["value"] == {"state_schema": schemas[index], "operations": operations[index], "boundary": "offline record adapter; no execution"}
        assert layer["M"]["value"] == {"kernel_commit": KERNEL, "adapter_edition": "1", "role": roles[index], "source_ids": refs[index]}
        for name in ("A", "E", "D", "Pi"):
            assert layer[name] == UNKNOWN
        assert layer["place"] == {name: UNKNOWN for name in ("r", "rho", "tau", "alpha", "c")}
        assert layer["K"] == {"status": "partial", "value": {"scope": "canonical-record-checks", "independently_recomputed": True,
                              "semantic_preservation": "not-assessed", "execution_authentication": "not-assessed"}}
    bridge = commitment_bindings(case["raw"], case["source"])
    params = [
        {"family_id": family["family_id"], "history_id": history["history_id"], "step_id": step["step_id"],
         "restriction_id": restriction["restriction_id"], "retained_member_ids": restriction["retained_member_ids"]},
        {"residual_family_id": history["residual_family_id"], "request_id": rr["request_id"], "result_id": rz["result_id"], "witness_id": rz["witness"]["witness_id"]},
        {"selected_member_id": selected, "graph_id": graph["graph_id"], "source_digest": bridge["qa4_source_digest"],
         "bundle_digest": digests["bundle"], "result_digest": digests["result"], "receipt_digest": digests["receipt"],
         "openqasm_digest": bridge["qa4_openqasm_digest"], "target": bridge["qa4_target"]},
    ]
    edges = result["edge_records"]
    assert len(edges) == 3
    for index, edge in enumerate(edges):
        assert set(edge) == {"schema", "edge_id", "kind", "from_layer_id", "to_layer_id", "rule", "state_refs", "parameters", "field_disposition", "introduced_variation", "unresolved", "validation_scope"}
        assert edge["schema"] == "e7q.ir.receipt-binding-edge/v0alpha1"
        assert edge["edge_id"] == identified_digest(edge, "edge_id")
        assert edge["kind"] == ["generates-metadata", "generates-metadata", "references-evidence"][index]
        assert edge["kind"] not in RELATION_KINDS
        assert edge["from_layer_id"] == layers[[0, 2, 3][index]]["layer_id"]
        assert edge["to_layer_id"] == layers[[2, 3, 4][index]]["layer_id"]
        assert edge["rule"] == {"id": ["qa4.restrict-metadata", "qa4.rank-metadata", "qa4.link-supplied-bytes"][index], "edition": "1"}
        assert edge["state_refs"] == [[history["history_id"], step["step_id"], restriction["restriction_id"]], refs[3], [selected, graph["graph_id"]]][index]
        assert edge["parameters"] == params[index]
        assert edge["field_disposition"] == DISPOSITIONS
        assert edge["unresolved"] == UNRESOLVED
        assert edge["introduced_variation"] == ["restricted-member-inventory", "ranked-best-inventory", "supplied-evidence-reference"][index]
        assert edge["validation_scope"] == ["recomputed-restriction", "recomputed-integer-ranking", "supplied-byte-and-target-linkage"][index]
    witness = result["witness"]
    assert set(witness) == {"schema", "witness_id", "realisation_witness_id", "selected_member_id", "source_digest", "receipt_graph_id", "evidence_digests", "openqasm_digest", "target", "layer_ids", "edge_ids"}
    assert witness["schema"] == "e7q.ir.receipt-binding-witness/v0alpha1"
    assert witness["witness_id"] == identified_digest(witness, "witness_id")
    assert witness["realisation_witness_id"] == rz["witness"]["witness_id"]
    assert witness["selected_member_id"] == selected
    assert witness["source_digest"] == bridge["qa4_source_digest"]
    assert witness["receipt_graph_id"] == graph["graph_id"]
    assert witness["evidence_digests"] == digests
    assert witness["openqasm_digest"] == bridge["qa4_openqasm_digest"]
    assert witness["target"] == bridge["qa4_target"]
    assert witness["layer_ids"] == [layer["layer_id"] for layer in layers]
    assert witness["edge_ids"] == [edge["edge_id"] for edge in edges]
    schema_validator.validate(result)


@pytest.mark.parametrize("mode", ["all", "partial"])
def test_joint_correlations_and_actual_retained_inventory(case, mode):
    planning_case(case, keep=mode)
    result = assess(case)
    assert_outcome(result, "bound")
    assert result["edge_records"][0]["parameters"]["retained_member_ids"] == case["restriction"]["retained_member_ids"]
    assert result["selected_member_id"] in case["restriction"]["retained_member_ids"]
    assert all(set(member["bindings"]) == {"qa4_source_digest", "qa4_bundle_digest", "qa4_openqasm_digest", "qa4_target", "label"} for member in case["family"]["members"])


@pytest.mark.parametrize("terminal", ["ambiguous", "empty", "invalid_input", "domain_error", "unsupported", "resource_limit"])
def test_nonunique_and_terminal_are_unbound_without_any_evidence_access(case, terminal, monkeypatch, schema_validator):
    if terminal == "ambiguous":
        planning_case(case, vectors=[(1,), (1,), (1,)])
    elif terminal == "empty":
        planning_case(case, keep="none")
    else:
        planning_case(case, terminal=terminal)
    assert case["rz"]["outcome"] == terminal
    no_evidence(monkeypatch)
    result = assess(case)
    assert_outcome(result, "unbound")
    assert result["realisation_outcome"] == terminal
    assert result["realisation_request_id"] == case["rr"]["request_id"]
    assert result["realisation_result_id"] == case["rz"]["result_id"]
    assert result["source_family_id"] == case["rz"]["source_family_id"]
    assert result["history_id"] == case["rz"]["history_id"]
    assert result["restriction_id"] == case["rz"]["restriction_id"]
    assert result["input_residual_family_id"] == case["rz"]["input_residual_family_id"]
    assert result["best_member_ids"] == case["rz"]["best_member_ids"] if terminal == "ambiguous" else result["best_member_ids"] == []
    assert result["source_digest"] is result["receipt_graph_id"] is None
    schema_validator.validate(result)
    assert validate_result(result, case) is None


@pytest.mark.parametrize("extra", ["source_digest", "receipt_graph_id", "source_bytes", "receipt_graph"])
def test_nonunique_rejects_extraneous_evidence_without_touching_it(case, extra, monkeypatch):
    planning_case(case, vectors=[(1,), (1,), (1,)])
    no_evidence(monkeypatch)
    if extra in {"source_digest", "receipt_graph_id"}:
        case["request"][extra] = FOREIGN
        rehash(case["request"], "request_id")
        result = assess(case)
    else:
        result = binding.assess_receipt_binding(case["request"], case["family"], case["history"], case["rr"], case["rz"], case["restriction"],
                                                **{extra: case["source"] if extra == "source_bytes" else case["graph"]})
    assert_outcome(result, "invalid_input")


@pytest.mark.parametrize("field", ["profile", "kernel_commit", "edition-family", "edition-history", "edition-realisation", "edition-rgp"])
def test_wellformed_alternative_profile_pin_editions_are_unsupported_before_evidence(case, field, monkeypatch):
    if field.startswith("edition-"):
        case["request"]["editions"][field.removeprefix("edition-")] = "alternative-edition"
    else:
        case["request"][field] = "alternative-profile"
    rehash(case["request"], "request_id")
    assert binding.validate_receipt_binding_request(case["request"]) is None
    no_evidence(monkeypatch)
    result = assess(case)
    assert_outcome(result, "unsupported")
    assert result["request_id"] == case["request"]["request_id"]
    assert result["realisation_request_id"] is result["source_digest"] is result["receipt_graph_id"] is None


@pytest.mark.parametrize("field,value,outcome", [
    ("profile", "", "invalid_input"), ("profile", 1, "invalid_input"),
    ("profile", "é" * 65, "resource_limit"), ("kernel_commit", "x" * 129, "resource_limit"),
    ("context", "é" * 513, "resource_limit"), ("inquiry", "x" * 1025, "resource_limit"),
    ("context", "\ud800", "invalid_input"), ("source_digest", "sha256:" + "A" * 64, "invalid_input"),
    ("realisation_result_id", None, "invalid_input"), ("receipt_graph_id", True, "invalid_input"),
])
def test_request_scalar_admission_before_hashing(case, field, value, outcome):
    kwargs = {key: case["request"][key] for key in ("realisation_request_id", "realisation_result_id", "context", "inquiry", "source_digest", "receipt_graph_id")}
    kwargs[field] = value
    error(outcome, binding.build_receipt_binding_request, **kwargs)


@pytest.mark.parametrize("name,ceiling", [("max_graph_bytes", 16 * 1024 * 1024), ("max_artifacts", 64), ("max_relations", 128), ("max_source_bytes", 1048576)])
@pytest.mark.parametrize("value", [True, False, 0, -1, 1.0, "1", None, "over"])
def test_declared_limits_require_exact_positive_ints_within_ceiling(case, name, ceiling, value):
    value = ceiling + 1 if value == "over" else value
    kwargs = {key: case["request"][key] for key in ("realisation_request_id", "realisation_result_id", "context", "inquiry", "source_digest", "receipt_graph_id")}
    error("invalid_input", binding.build_receipt_binding_request, **kwargs, **{name: value})


@pytest.mark.parametrize("field", ["request_id", "schema", "extra", "limits-extra", "editions-extra", "editions-missing"])
def test_request_whole_validation_refuses_stale_identity_and_extra_properties(case, field):
    request = copy.deepcopy(case["request"])
    if field == "request_id":
        request[field] = FOREIGN
    elif field == "schema":
        request[field] = "other-schema"
    elif field == "limits-extra":
        request["limits"]["surprise"] = 1
    elif field == "editions-extra":
        request["editions"]["surprise"] = "1"
    elif field == "editions-missing":
        del request["editions"]["rgp"]
    else:
        request[field] = "inert secret which must not be echoed"
    if field != "request_id":
        rehash(request, "request_id")
    error("invalid_input", binding.validate_receipt_binding_request, request)
    case["request"] = request
    result = assess(case)
    assert_outcome(result, "invalid_input")
    assert result["request_id"] is None


@pytest.mark.parametrize("field", ["qa4_source_digest", "qa4_bundle_digest", "qa4_openqasm_digest", "qa4_target"])
def test_each_missing_reserved_key_is_unsupported_but_upstream_family_valid(case, field):
    bridge = commitment_bindings(case["raw"], case["source"])
    del bridge[field]
    planning_case(case, alternatives=[dict(bridge, label="a")])
    assert validate_candidate_family(case["family"]) is None
    assert case["rz"]["outcome"] == "unique"
    assert_outcome(assess(case), "unsupported")


@pytest.mark.parametrize("field,value", [
    ("qa4_source_digest", "sha256:" + "A" * 64), ("qa4_bundle_digest", "not-a-digest"),
    ("qa4_openqasm_digest", "sha256:" + "0" * 63), ("qa4_target", "é" * 65),
    ("qa4_target", "\ud800"),
])
def test_malformed_reserved_values_are_invalid_not_unsupported(case, field, value):
    # Surrogates cannot form a valid upstream identity, so probe the assessor
    # directly rather than forcing the old builder to serialize invalid UTF-8.
    if value == "\ud800":
        case["family"]["members"][0]["bindings"][field] = value
    else:
        bridge = commitment_bindings(case["raw"], case["source"])
        bridge[field] = value
        planning_case(case, alternatives=[dict(bridge, label="a")])
    assert_outcome(assess(case), "invalid_input")


@pytest.mark.parametrize("field", ["qa4_source_digest", "qa4_bundle_digest", "qa4_openqasm_digest", "qa4_target"])
def test_each_wellformed_but_contradictory_reserved_commitment_is_invalid(case, field):
    bridge = commitment_bindings(case["raw"], case["source"])
    bridge[field] = "different-target" if field == "qa4_target" else FOREIGN
    planning_case(case, alternatives=[dict(bridge, label="a")])
    assert_outcome(assess(case), "invalid_input")


@pytest.mark.parametrize("field", ["selected_member_id", "best_member_ids", "witness", "extra", "message", "result_id"])
def test_rehashed_q_a3_forgery_is_not_an_unbound_declaration(case, field, monkeypatch):
    rz = case["rz"]
    if field == "selected_member_id":
        rz[field] = FOREIGN
    elif field == "best_member_ids":
        rz[field] = [FOREIGN]
    elif field == "witness":
        rz[field]["best_value_vector"] = [-10]
        rehash(rz[field], "witness_id")
    else:
        rz[field] = FOREIGN
    if field != "result_id":
        rehash(rz, "result_id")
    request_for(case)
    no_evidence(monkeypatch)
    result = assess(case)
    assert_outcome(result, "invalid_input")
    assert result["realisation_result_id"] is None


@pytest.mark.parametrize("which", ["foreign", "excluded"])
def test_hash_shaped_foreign_or_excluded_winner_is_not_selected(case, which, monkeypatch):
    planning_case(case, keep="partial")
    winner = FOREIGN if which == "foreign" else case["restriction"]["excluded_member_ids"][0]
    case["rz"]["selected_member_id"] = winner
    case["rz"]["best_member_ids"] = [winner]
    case["rz"]["witness"]["best_member_ids"] = [winner]
    rehash(case["rz"]["witness"], "witness_id")
    rehash(case["rz"], "result_id")
    request_for(case)
    no_evidence(monkeypatch)
    assert_outcome(assess(case), "invalid_input")


@pytest.mark.parametrize("field", ["context", "inquiry", "realisation_request_id", "realisation_result_id", "source_digest", "receipt_graph_id"])
def test_request_linkage_must_match_actual_backing(case, field, monkeypatch):
    request_for(case, **{field: "different context" if field in {"context", "inquiry"} else FOREIGN})
    no_evidence(monkeypatch)
    result = assess(case)
    assert_outcome(result, "invalid_input")
    assert result["source_digest"] is result["receipt_graph_id"] is None


@pytest.mark.parametrize("source", [None, bytearray(b"inert source bytes\n"), "inert source bytes\n", b"inert source bytes", b"inert source bytes\r\n"])
def test_source_exact_type_and_no_normalization(case, source):
    case["source"] = source
    assert_outcome(assess(case), "invalid_input")


@pytest.mark.parametrize("kind", ["target", "shots", "openqasm", "source", "whitespace"])
def test_separately_consistent_changed_carriers_do_not_match_old_commitment(case, kind, tmp_path):
    kwargs = {"source": case["source"]}
    if kind == "target":
        kwargs["target"] = "different-target"
    elif kind == "shots":
        kwargs["shots"] = 5
    elif kind == "openqasm":
        kwargs["openqasm"] = "OPENQASM 2.0;  // inert supplied text\n"
    elif kind == "source":
        kwargs["source"] += b" "
    else:
        kwargs["spaced"] = True
    raw = inert_carriers(**kwargs)
    graph = mapped_graph(tmp_path, raw)
    assert workflow.validate_legacy_receipt_evidence(graph)["status"] == "PASS"
    if kind == "whitespace":
        assert json.loads(raw["bundle"]) == json.loads(case["raw"]["bundle"])
        assert raw["bundle"] != case["raw"]["bundle"]
    case["graph"] = graph
    request_for(case)
    assert_outcome(assess(case), "invalid_input")


@pytest.mark.parametrize("status", ["FAIL", "BLOCKED", "UNSUPPORTED", "NOT_ASSESSED", "unknown"])
def test_real_supplied_nonpass_receipt_status_maps_to_invalid(case, status, tmp_path):
    receipt = json.loads(case["raw"]["receipt"])
    receipt["status"] = status
    raw = dict(case["raw"], receipt=encoded(receipt))
    case["graph"] = mapped_graph(tmp_path, raw)
    report = workflow.validate_legacy_receipt_evidence(case["graph"])
    assert report["status"] != "PASS"
    request_for(case)
    assert_outcome(assess(case), "invalid_input")


@pytest.mark.parametrize("mutation", ["counts", "probabilities", "bundle_digest", "target", "proof"])
def test_raw_pass_receipt_is_not_trusted_over_recomputation(case, mutation, tmp_path):
    receipt = json.loads(case["raw"]["receipt"])
    if mutation == "counts":
        receipt[mutation] = {"1": 4}
    elif mutation == "probabilities":
        receipt[mutation] = {"0": 0.0}
    elif mutation == "proof":
        receipt[mutation][0]["source_digest"] = FOREIGN
    else:
        receipt[mutation] = FOREIGN
    assert receipt["status"] == "PASS"
    case["graph"] = mapped_graph(tmp_path, dict(case["raw"], receipt=encoded(receipt)))
    assert workflow.validate_legacy_receipt_evidence(case["graph"])["status"] != "PASS"
    request_for(case)
    assert_outcome(assess(case), "invalid_input")


@pytest.mark.parametrize("report", [
    {"status": "FAIL", "checks": []}, {"status": "BLOCKED", "checks": []},
    {"status": "UNSUPPORTED", "reason": "unsupported_count_label_order", "checks": []},
    {"status": "NOT_ASSESSED", "checks": []}, {"status": "unknown", "checks": []},
    {"checks": []}, None, [], "PASS", {"status": True, "checks": []},
    {"status": "PASS", "checks": [{"name": "required", "passed": False}]},
    {"status": "PASS", "checks": [{"name": "required", "passed": 1}]},
    {"status": "PASS", "checks": [{"name": "required", "passed": True}, {"name": "contradiction", "passed": False}]},
    {"status": "PASS", "checks": "malformed"}, {"status": "PASS"},
])
def test_public_legacy_report_requires_exact_pass_and_uncontradicted_checks(case, report, monkeypatch):
    monkeypatch.setattr(binding, "validate_legacy_receipt_evidence", lambda graph: copy.deepcopy(report))
    assert_outcome(assess(case), "invalid_input")


@pytest.mark.parametrize("value,outcome", [("another-wellformed-workflow/v1", "unsupported"), (None, "invalid_input"), (17, "invalid_input"), ("", "invalid_input")])
def test_workflow_dialect_support_is_separate_from_structural_graph_admission(case, value, outcome):
    case["graph"]["extensions"]["workflow_format"] = value
    rehash(case["graph"], "graph_id")
    assert validate_graph(case["graph"], level="F1")["status"] == "PASS"
    request_for(case)
    assert_outcome(assess(case), outcome)


@pytest.mark.parametrize("kind", ["missing-role", "duplicate-role", "foreign-role", "stale-graph", "bad-base64", "bad-digest", "bad-length"])
def test_structural_graph_and_role_recovery_never_trust_imported_pass(case, kind):
    graph = case["graph"]
    if kind == "missing-role":
        del graph["extensions"]["source_refs"]["receipt"]
    elif kind == "duplicate-role":
        graph["extensions"]["source_refs"]["receipt"] = graph["extensions"]["source_refs"]["bundle"]
    elif kind == "foreign-role":
        graph["extensions"]["source_refs"]["receipt"] = "inert:missing"
    elif kind == "stale-graph":
        graph["name"] += " changed"
    else:
        source = next(artifact for artifact in graph["artifacts"] if artifact["kind"] == "source")
        if kind == "bad-base64":
            source["payload"]["content_base64"] = "%%invalid%%"
        elif kind == "bad-digest":
            source["payload"]["content_digest"] = FOREIGN
        else:
            source["payload"]["byte_length"] += 1
    if kind != "stale-graph":
        rehash(graph, "graph_id")
    request_for(case)
    assert_outcome(assess(case), "invalid_input")


@pytest.mark.parametrize("limit", ["max_graph_bytes", "max_artifacts", "max_relations", "max_source_bytes"])
def test_exact_admitted_budgets_and_one_under_are_resource_not_empty(case, limit, monkeypatch):
    graph = case["graph"]
    endpoints = {"max_graph_bytes": len(canonical_bytes(graph)), "max_artifacts": len(graph["artifacts"]),
                 "max_relations": len(graph["relations"]), "max_source_bytes": max(len(case["source"]), *(len(raw) for raw in case["raw"].values()))}
    request_for(case, **{limit: endpoints[limit]})
    assert_outcome(assess(case), "bound")
    request_for(case, **{limit: endpoints[limit] - 1})
    if limit == "max_source_bytes":
        def forbidden(graph):
            pytest.fail("Carrier limit must precede receipt parsing/recomputation")
        monkeypatch.setattr(binding, "validate_legacy_receipt_evidence", forbidden)
    else:
        no_evidence(monkeypatch)
    result = assess(case)
    assert_outcome(result, "resource_limit")
    assert result["realisation_outcome"] == "unique"


def test_original_source_size_is_checked_before_any_graph_access(case, monkeypatch):
    request_for(case, max_source_bytes=len(case["source"]) - 1)
    no_evidence(monkeypatch)
    assert_outcome(assess(case), "resource_limit")


def test_each_recovered_carrier_length_checked_before_evidence_validator(case, monkeypatch):
    limit = max(len(case["source"]), 32)
    request_for(case, max_source_bytes=limit)
    calls = []
    def recovered(graph, ref):
        calls.append(ref)
        return b" " * (limit + 1)
    monkeypatch.setattr(binding, "recover_legacy_source", recovered)
    monkeypatch.setattr(binding, "validate_legacy_receipt_evidence", lambda graph: pytest.fail("Late carrier check"))
    assert_outcome(assess(case), "resource_limit")
    assert calls


class CustomDict(dict):
    def items(self):
        pytest.fail("Custom container callback must not be invoked")


class CustomList(list):
    def __iter__(self):
        pytest.fail("Custom container callback must not be invoked")


@pytest.mark.parametrize("kind,outcome", [
    ("cycle", "invalid_input"), ("custom-dict", "invalid_input"), ("custom-list", "invalid_input"),
    ("iterator", "invalid_input"), ("nan", "invalid_input"), ("infinity", "invalid_input"),
    ("surrogate", "invalid_input"), ("nonstring-key", "invalid_input"),
    ("integer-over", "resource_limit"), ("integer-under", "resource_limit"), ("depth", "resource_limit"),
])
def test_graph_plain_finite_guard_precedes_f1_and_hashing(case, kind, outcome, monkeypatch):
    graph = case["graph"]
    if kind == "cycle":
        graph["extensions"]["adversarial"] = graph
    elif kind == "custom-dict":
        graph["extensions"]["adversarial"] = CustomDict(a=1)
    elif kind == "custom-list":
        graph["extensions"]["adversarial"] = CustomList([1])
    elif kind == "iterator":
        graph["extensions"]["adversarial"] = iter([1])
    elif kind == "depth":
        deep = 0
        for _ in range(65):
            deep = [deep]
        graph["extensions"]["adversarial"] = deep
    elif kind == "nonstring-key":
        graph["extensions"][17] = "inert"
    else:
        graph["extensions"]["adversarial"] = {"nan": float("nan"), "infinity": float("inf"),
                                               "surrogate": "\ud800", "integer-over": 2 ** 127 + 1,
                                               "integer-under": -(2 ** 127) - 1}[kind]
    no_evidence(monkeypatch)
    assert_outcome(assess(case), outcome)


@pytest.mark.parametrize("number", [2 ** 127, -(2 ** 127), True, 1, 1.0])
def test_graph_integer_endpoints_and_finite_builtin_json_scalars_remain_supported(case, number):
    case["graph"]["extensions"]["inert-number"] = number
    rehash(case["graph"], "graph_id")
    request_for(case)
    assert_outcome(assess(case), "bound")


@pytest.mark.parametrize("kind", ["individual-string", "utf8-total", "keys-total", "punctuation"])
def test_graph_small_budget_short_circuits_before_later_invalid_children(case, kind, monkeypatch):
    # Budget checks must reject the earlier supported oversized scalar/sum;
    # the later object is deliberately invalid, not traversed or serialized.
    request_for(case, max_graph_bytes=32)
    if kind == "individual-string":
        graph = {"a": "x" * 33, "later": object()}
    elif kind == "utf8-total":
        graph = {"a": "é" * 10, "b": "é" * 10, "later": object()}
    elif kind == "keys-total":
        graph = {"é" * 17: None, "later": object()}
    else:
        # String sum fits, exact JSON including punctuation does not.
        graph = {"a": [0] * 20}
    graph["graph_id"] = case["request"]["receipt_graph_id"]
    case["graph"] = graph
    no_evidence(monkeypatch)
    assert_outcome(assess(case), "resource_limit")


@pytest.mark.parametrize("mutation", ["target", "member", "layer", "edge", "edge-order", "layer-order", "witness-extra", "result-extra", "bool-int"])
def test_whole_result_validator_refuses_rehashed_adapter_forgery(case, mutation):
    result = assess(case)
    assert_outcome(result, "bound")
    if mutation == "target":
        result["witness"]["target"] = "different-target"
        rehash(result["witness"], "witness_id")
    elif mutation == "member":
        result["selected_member_id"] = FOREIGN
        result["best_member_ids"] = [FOREIGN]
    elif mutation == "layer":
        result["layer_records"][0]["place"]["r"] = {"status": "declared", "value": {"rank": 1}}
        rehash(result["layer_records"][0], "layer_id")
    elif mutation == "edge":
        result["edge_records"][2]["kind"] = "generates-metadata"
        rehash(result["edge_records"][2], "edge_id")
    elif mutation == "edge-order":
        result["edge_records"].reverse()
    elif mutation == "layer-order":
        result["layer_records"].reverse()
    elif mutation == "witness-extra":
        result["witness"]["extra"] = "inert"
        rehash(result["witness"], "witness_id")
    elif mutation == "bool-int":
        result["layer_records"][0]["K"]["value"]["independently_recomputed"] = 1
        rehash(result["layer_records"][0], "layer_id")
    else:
        result["extra"] = "inert"
    rehash(result, "binding_id")
    error("invalid_input", validate_result, result, case)


def test_objective_order_and_integer_endpoints_preserve_upstream_ranking(case):
    objectives = [{"id": name, "edition": "1", "direction": "min", "unit": "inert"} for name in ("first", "second")]
    vectors = [(-(2 ** 127), 2 ** 127 - 1), (2 ** 127 - 1, -(2 ** 127)), (0, 0)]
    planning_case(case, objectives=objectives, vectors=vectors)
    first = assess(case)
    assert_outcome(first, "bound")
    assert first["selected_member_id"] == case["restriction"]["retained_member_ids"][0]
    first_request = case["request"]["request_id"]
    planning_case(case, objectives=list(reversed(objectives)), vectors=[tuple(reversed(vector)) for vector in vectors])
    second = assess(case)
    assert_outcome(second, "bound")
    assert second["selected_member_id"] == case["restriction"]["retained_member_ids"][1]
    assert second["binding_id"] != first["binding_id"]
    assert case["request"]["request_id"] != first_request


def test_no_hidden_new_backing_family_or_history_string_cap(case):
    # Larger than request's 1024 bytes; valid inert Q-A1 bindings/metadata and
    # Q-A2 preservation declarations must not acquire the Q-A4 graph cap.
    graph_bytes = len(canonical_bytes(case["graph"]))
    inert = "z" * (graph_bytes + 1)
    bridge = commitment_bindings(case["raw"], case["source"])
    planning_case(case, alternatives=[dict(bridge, label=inert)], assumptions=[inert], limitations=[inert + "l"])
    step = case["history"]["steps"][0]
    step["preserves"] = [inert]
    rehash(step, "step_id")
    rehash(case["history"], "history_id")
    case["rr"]["history_id"] = case["history"]["history_id"]
    rehash(case["rr"], "request_id")
    case["rz"] = assess_realisation(case["rr"], case["family"], case["history"], case["restriction"])
    assert case["rz"]["outcome"] == "unique"
    request_for(case, max_graph_bytes=graph_bytes)
    assert_outcome(assess(case), "bound")


@pytest.mark.parametrize("field,value", [("context", "é" * 512), ("inquiry", "é" * 512), ("profile", "é" * 64)])
def test_exact_utf8_request_text_endpoints(case, field, value):
    request = request_for(case, **{field: value})
    assert binding.validate_receipt_binding_request(request) is None


def test_exact_utf8_target_endpoint_and_new_claim_identity(tmp_path):
    source = b"inert source bytes\n"
    raw = inert_carriers(source, target="é" * 64)
    graph = mapped_graph(tmp_path, raw)
    local = planning_case(dict(source=source, raw=raw, graph=graph))
    assert_outcome(assess(local), "bound")
    assert assess(local)["witness"]["target"] == "é" * 64


@pytest.mark.parametrize("mutation", ["missing-layer", "missing-edge", "missing-witness", "selected-null", "evidence-null", "unknown-component", "extra-place", "extra-edge", "bad-message", "unbound-with-evidence"])
def test_schema_rejects_outcome_and_nested_shape_contradictions(case, schema_validator, mutation):
    result = assess(case)
    assert_outcome(result, "bound")
    if mutation == "missing-layer":
        result["layer_records"].pop()
    elif mutation == "missing-edge":
        result["edge_records"].pop()
    elif mutation == "missing-witness":
        result["witness"] = None
    elif mutation == "selected-null":
        result["selected_member_id"] = None
    elif mutation == "evidence-null":
        result["evidence_digests"] = None
    elif mutation == "unknown-component":
        result["layer_records"][0]["A"] = {"status": "declared", "value": {}}
    elif mutation == "extra-place":
        result["layer_records"][0]["place"]["depth"] = UNKNOWN
    elif mutation == "extra-edge":
        result["edge_records"][0]["rule"]["callback"] = "never"
    elif mutation == "bad-message":
        result["message"] = "accepted execution"
    else:
        result["outcome"] = "unbound"
        result["message"] = MESSAGES["unbound"]
    rehash(result, "binding_id")
    assert list(schema_validator.iter_errors(result)), mutation


@pytest.mark.parametrize("outcome", ["invalid_input", "unsupported", "resource_limit"])
def test_refusal_results_are_schema_valid_and_never_partial_witnesses(case, outcome, schema_validator):
    if outcome == "invalid_input":
        case["request"]["request_id"] = FOREIGN
    elif outcome == "unsupported":
        request_for(case, profile="different-profile")
    else:
        request_for(case, max_graph_bytes=1)
    result = assess(case)
    assert_outcome(result, outcome)
    schema_validator.validate(result)
    assert validate_result(result, case) is None


@pytest.mark.parametrize("role", ["bundle", "result", "receipt"])
def test_each_individual_carrier_budget_precedes_evidence_validation(case, role, monkeypatch):
    limit = max(len(case["source"]), *(len(raw) for raw in case["raw"].values()))
    request_for(case, max_source_bytes=limit)
    calls = []
    def recovered(graph, ref):
        calls.append(ref)
        if ref == graph["extensions"]["source_refs"][role]:
            return b" " * (limit + 1)
        return workflow.recover_legacy_source(graph, ref)
    monkeypatch.setattr(binding, "recover_legacy_source", recovered)
    monkeypatch.setattr(binding, "validate_legacy_receipt_evidence", lambda graph: pytest.fail("Evidence parsed before all role limits"))
    assert_outcome(assess(case), "resource_limit")
    assert case["graph"]["extensions"]["source_refs"][role] in calls


@pytest.mark.parametrize("mutation", ["bad-base64", "bad-digest", "bad-length", "duplicate-source", "missing-source"])
def test_f1_valid_source_carriers_must_recover_before_evidence_assessment(case, mutation, monkeypatch):
    sources = [copy.deepcopy(artifact) for artifact in case["graph"]["artifacts"] if artifact["kind"] == "source"]
    source = next(artifact for artifact in sources if artifact["payload"]["role"] == "bundle")
    if mutation == "bad-base64":
        source["payload"]["content_base64"] = "%%invalid%%"
    elif mutation == "bad-digest":
        source["payload"]["content_digest"] = FOREIGN
    elif mutation == "bad-length":
        source["payload"]["byte_length"] += 1
    elif mutation == "missing-source":
        sources.remove(source)
    else:
        duplicate = copy.deepcopy(source)
        duplicate["payload"]["display_name"] = "different envelope, same stable source ref"
        rehash(duplicate, "artifact_id")
        sources.append(duplicate)
    rehash(source, "artifact_id")
    graph = build_graph(sources, [], name="F1-valid adversarial supplied sources",
                        extensions=copy.deepcopy(case["graph"]["extensions"]))
    assert validate_graph(graph, level="F1")["status"] == "PASS"
    case["graph"] = graph
    request_for(case)
    monkeypatch.setattr(binding, "validate_legacy_receipt_evidence", lambda graph: pytest.fail("Evidence validator preceded carrier recovery"))
    assert_outcome(assess(case), "invalid_input")


def test_graph_visited_value_bound_uses_small_shared_fixture(case, monkeypatch):
    # 512+400 slots allocated, but >200,000 visits after alias expansion.
    leaf = [None] * 512
    case["graph"]["extensions"]["inert-shared"] = [leaf] * 400
    no_evidence(monkeypatch)
    assert_outcome(assess(case), "resource_limit")


def test_noncyclic_shared_graph_objects_are_not_rejected_as_cycles(case):
    leaf = [True, None, "inert"]
    case["graph"]["extensions"]["inert-shared"] = [leaf, leaf]
    rehash(case["graph"], "graph_id")
    request_for(case)
    assert_outcome(assess(case), "bound")


def test_python_equal_bool_integer_result_without_rehash_still_rejected(case):
    original = assess(case)
    forged = copy.deepcopy(original)
    forged["layer_records"][0]["K"]["value"]["independently_recomputed"] = 1
    assert forged == original  # Python equality loses the exact JSON type.
    assert canonical_bytes(forged) != canonical_bytes(original)
    error("invalid_input", validate_result, forged, case)


@pytest.mark.parametrize("mutation", [
    "missing-reason", "integer-reason", "empty-reason", "bool-status", "missing-status", "null-checks", "missing-checks",
    "missing-name", "integer-name", "missing-passed", "string-passed", "integer-passed", "failed-check", "mixed-failed",
    "missing-message", "integer-message", "scalar-check",
])
def test_plausible_pass_report_with_malformed_required_fields_is_invalid(case, mutation, monkeypatch):
    report = copy.deepcopy(workflow.validate_legacy_receipt_evidence(case["graph"]))
    assert report["status"] == "PASS"
    assert report["checks"]
    if mutation == "missing-reason":
        del report["reason"]
    elif mutation == "integer-reason":
        report["reason"] = 1
    elif mutation == "empty-reason":
        report["reason"] = ""
    elif mutation == "bool-status":
        report["status"] = True
    elif mutation == "missing-status":
        del report["status"]
    elif mutation == "null-checks":
        report["checks"] = None
    elif mutation == "missing-checks":
        del report["checks"]
    elif mutation == "failed-check":
        report["checks"][0]["passed"] = False
    elif mutation == "mixed-failed":
        assert all(check["passed"] is True for check in report["checks"])
        report["checks"].append({"name": "contradiction", "passed": False, "message": "inert failed required check"})
    elif mutation == "scalar-check":
        report["checks"][0] = True
    else:
        action, field = mutation.split("-", 1)
        if action == "missing":
            del report["checks"][0][field]
        else:
            report["checks"][0][field] = "true" if action == "string" else 1
    monkeypatch.setattr(binding, "validate_legacy_receipt_evidence", lambda graph: report)
    assert_outcome(assess(case), "invalid_input")
