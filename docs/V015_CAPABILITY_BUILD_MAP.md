# E7Q-IR and E7Q v0.15 capability build map

Source for new planning: E7G-T v0.15/MSC1, `E7G-T_Kernel_v0.15_Experimental_Canonical_Reference.md`, merge `2cba2045bb22036ce489083a5ac853a9d867eb21`, SHA-256 `5b1e9913cf24b80612f81014b8cc7efc7574d43402a2a188a17daa096c0c621a`. Direction proposal: `E7-ECO-DIR-2026-09-25.1` in central E7-Ecosystem PR #9. Existing v0.12.1 artifacts and this repository's prior adoption record remain pinned until a separate reviewed migration. Source inclusion, product adoption and implementation conformance are different decisions.

Read the source's §X.14–X.21 and applicable conformance matrices before an adapter. `adopted`, `experimental`, `deferred` and `not_applicable` below are **planning dispositions**, not claims that v0.15 code exists. Record `retain/adapt/replace/retire` separately for native components; nothing in this map changes a native format or API. WPC/0.1 WC0–WC4 remains distinct from WPC-Core/0.2, and RGP2 remains a revision of historical RGP/0.1, not the RGP/0.2 profile.

E7Q-IR owns candidate planning, ordered compiler transformations and receipts. E7Q owns native physical quantum semantics. The current Q-A1/Q-A2 records retain their exact editions; Q-A3 realisation and Q-A4 receipt binding remain separate gates. No kernel profile supplies quantum amplitudes, physical measurement or speed advantage.

## Component dispositions and exact gates

| v0.15 component | New-work posture | Native mapping / preservation | Adversarial or boundary gate |
|---|---|---|---|
| EEC-Q/0.1 | experimental | planning; Formal rational construction only; keep correlated Joint rows and signed coefficients exact. Never treat them as quantum amplitudes or evidence weights. | Same marginals/different Joint tables must yield different candidate paths; invalid cancellation and zero/empty/failure remain distinct. |
| SF/0.1 | experimental | planning; Shared circuit/layout/target/calibration assignments and criterion-bound realisation. | Two dependent assignments must not become a four-row independent product; no-feasible outcome is typed. |
| CFS/0.1 | experimental | planning; SF-outside/EEC-inside only where a formal EEC state actually exists; native quantum state remains separate. | Reverse nesting and coefficient-to-measurement coercion rejected. |
| RGP/0.2 | experimental | design; Q-A4 may bind source, generation/transform edge, layer and exact receipt edition; no current /0.2 runtime claim. | Hosting differs from generation, SR0 locator differs from SR4 source-bearing encoding, rank differs from execution time. |
| WPC-Core/0.2 | deferred | candidate; A full compilation construction may have portions, relations and constraints independent of how per-pass artifacts encode it. | Constituted but unencoded whole; stale portion and pairwise-pass/global-fail compilation constraints. |
| WPC-Evolution/0.1 | deferred | An optimizer candidate is not a committed successor. | Uncommitted candidate cannot replace accepted compilation history. |
| WPC-Distributed/0.1 | not_applicable | unsupported; No distributed WPC model declared by E7Q-IR. | Do not infer consensus from parallel backends. |
| REC/0.1 | deferred | A future evidence receipt may separately track support/refutation, scope, time and replay; existing Proof-of-Path is not REC. | Signed coefficient or hash cannot turn an unsupported hardware claim into support. |
| MSC/0.1 | deferred | candidate; Potential typed comparisons among program, compiled circuit and hardware context require explicit carriers and common-codomain maps. | Link-wise compatibility must not be reported as a global executable mapping; resource limit is not incompatibility. |

## Ordered work and acceptance

1. Preserve Q-A1/Q-A2 exact family and ordered history; compare one plain candidate table to the dependent representation.
2. Implement/review Q-A3 residual-family realisation with resource and no-feasible outcomes; prove the selected mapping belongs to the residual family.
3. Design Q-A4 exact source, transform, target and observation receipt under declared RGP/0.2 semantics. Treat WPC/REC/MSC as separate opt-in studies with their own criteria and negative cases.
4. Reproduce at an exact head, verify legacy IDs/serialisation and quantum-specific semantics unchanged, and independently review any adoption. No full E7C, quantum advantage or new backend claim.

Cross-product exchange, if used, requires the same released contract at
two independent consumers without changing native meanings. A passing test
or model output is not general E7C fidelity, mathematical source truth,
authorization, improved intelligence, production readiness or product value.
Recheck current main and open PR writers at each milestone.
