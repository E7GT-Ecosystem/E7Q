# E7Q-IR commercial licensing policy

Owner-selected direction: 2026-10-14. Builder: Codex.
Implementation baseline: `c519484bccdbe411b05acdba9c24ef1cd852d041` (merged Q-A3 / PR #84).

## Boundary and effective scope

E7Q has a public Apache-2.0 implementation and CC-BY-SA-4.0 documentation.
The next commercial E7Q-IR implementation is a separately designated
**source-available** component. Its public software terms are the unmodified
**PolyForm Noncommercial License 1.0.0**, with a separately executed commercial
agreement for uses outside those terms. There is no ShareAlike or source-publication
obligation added by this policy. Required notices and licence conditions still apply.

The terms become applicable to a new component when the rights holder publishes
that component with its explicit licence designation. This policy does not
relicense existing E7Q-IR files, add restrictions to Apache permissions or revoke
prior grants. Current `src/e7q/ir/`, including Q-A3, remains Apache-2.0.
Current schemas and documentation retain their existing terms. A public PR is
also a publication surface; delaying its merge does not retract a licence grant.

| Material | Applicable terms |
|---|---|
| Published E7Q software and approved open-core maintenance | Apache-2.0, with existing notices |
| Existing specifications/documentation | CC-BY-SA-4.0 unless a file states otherwise |
| New designated implementation under `commercial/e7q_ir/` | PolyForm-Noncommercial-1.0.0; separately negotiated commercial rights |
| Third-party software/content | Its original licence, even when used by a commercial component |
| Abstract ideas, facts and independently written interoperable implementations | No exclusive ownership is asserted by this policy |

`commercial/e7q_ir/` presently contains **no commercial implementation**. There
is no paywall on the current Python package and no commercial capability is
claimed shipped. Merely importing E7Q's open interfaces does not make another
program subject to the commercial licence. A changed path, file name or label
does not eliminate rights in previously published content.

## Public permissions and commercial route

The [complete software licence](../../commercial/e7q_ir/LICENSE) controls,
not this explanatory summary. In particular:

- Any noncommercial purpose is permitted under the licence.
- Personal research/experimentation/study without anticipated commercial
  application is expressly permitted.
- The listed charitable, educational, public research, public safety/health,
  environmental and government organisations have the licence's express
  permitted-use scope, regardless of funding. Do not narrow those exceptions
  through a summary or call every funded activity paid commercial use.
- Modification and distribution are permitted within the licence's terms;
  distribute required notices and the licence/URL. There is no requirement to
  publish modifications.
- Corporate evaluation is not automatically an unlimited free production
  grant. If its intended purpose falls outside the public licence, request a
  written evaluation or commercial agreement before using the designated code.

For uses outside the public grant, ask the maintainer for a commercial agreement.
The repository's designated contact is **oleksandr@e7gt.com**, subject to the
rights holder confirming the licensing counterparty. No agreement, fee,
subscription or entitlement is created by opening an issue, making contact,
downloading code or paying without an executed agreement.

Negotiated agreements must identify the licensor's authority, exact component
and version, customer/legal entities, duration, fees, permitted internal
production, integration, redistribution and hosted-service uses, modification
rights, affiliate/contractor access, notices, support/warranty/security scope,
termination and applicable law. These are negotiation subjects, not an executed
contract or guarantees supplied by this policy. Preserve third-party grants.

## Contributor and publication gate

Do not publish commercially sensitive new implementation under the blanket
Apache declaration as a temporary measure. Develop it separately and use the
commercial directory only after rights clearance. No private code or collaborator
material is authorised for publication by this policy.

Before a designated component's first publication:

1. Record original authorship/right-to-license evidence and any assignments or
   written grants needed for commercial distribution; author metadata is not proof.
2. Review copied material, dependencies and adapted CC-BY-SA content. Preserve
   notices and satisfy applicable terms; independent ideas are distinct from copied text.
3. Record the component path, content SHA-256, rights basis and review reference
   in `docs/licensing/component-register.json`; add the SPDX identifier and
   required notice to each implementation file.
4. Put an appropriate licence and notices in its separate distribution. Do not
   include it in an Apache-only E7Q wheel/source archive or implicitly import it.
5. Obtain a written contributor agreement before accepting outside contributions
   to the commercial component. It must authorise the intended public and
   commercial licensing. No assignment or such permission is inferred from a PR.

Open-core IR additions/changes require an explicit, hash-bound `retain_public_terms`
decision in the register. Retain Apache-2.0 for code and existing specification
terms for schemas; a decision does not waive third-party ShareAlike obligations. This makes the publication choice visible; it cannot
prove the reviewer had authority or prevent a determined maintainer bypass.
Existing licence grants always survive this internal gate.

## Reconciliation and controls

- Retain all current quantum semantics, APIs, schemas, identities and kernel pins.
- Adapt licensing notices and contribution/publication procedures only.
- Add standard commercial terms and a separate packaging boundary.
- EEC-Q/SF/CFS/RGP dispositions remain as recorded in the build plan. v0.15 is
  the requested conceptual direction; this change does not migrate older pins.
- PR #85's external evidence documentation is separate and must not be rewritten.

`python scripts/check_licensing_boundary.py` checks the declared publication
boundary, exact protected licence documents, reviewed hashes and package discovery.
CI runs it and its negative controls. It is not legal enforcement, infringement
detection, a CLA signature service or an ownership/dependency audit.

Before accepting commercial contributions or signing customer terms, complete
the outstanding rights review in [RIGHTS_REVIEW.md](RIGHTS_REVIEW.md), including
the PolyForm patent grant and organisation exceptions. The selected public
licence text is used verbatim, rather than replaced by an improvised legal form.
