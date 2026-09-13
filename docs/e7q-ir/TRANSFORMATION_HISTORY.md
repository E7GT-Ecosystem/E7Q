# Ordered transformation history

Status: Q-A2 bounded contract, `v0alpha1`.

`e7q.ir.transformation-history/v0alpha1` records lowering, identification,
restriction, routing, scheduling or binding steps in exact order. Every step
binds its rule and edition, input family, admitted domain, explicit exclusions,
preservation, loss, limitations, outcome and—only on success—output family.

The contract preserves `invalid_input`, `domain_error`, `unsupported` and
`resource_limit` as terminal non-success outcomes. They are not empty families
and cannot publish an output family. A strict transform cannot hide excluded
members; explicit pruning is a `restrict` step with an exclusion inventory.

History identity is order-sensitive. A history must form one continuous family
chain and must stop at the first non-success outcome. Canonical validation
rebuilds every step and the full history, rejecting stale identities.

This layer records declared execution structure. It does not prove that a rule
is quantum-semantically correct, that the declared domain is complete, that a
candidate is feasible or optimal, or that hardware produced any result. Q-A3
must bind a selected member to the residual family under declared ordered
objectives; Q-A4 must bind that realisation and native evidence into a receipt.
