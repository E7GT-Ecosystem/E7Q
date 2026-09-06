# E7Q-IR Security and Trust Boundary

E7Q-IR v0alpha1 treats supplied circuit and result files as data. The external
workflow builder reads and hashes them but does not import Python, execute
archives, submit jobs, or run supplied quantum programs.

Separate trust dimensions must remain visible:

- content integrity;
- actor identity;
- chronology;
- provider attribution;
- semantic correctness;
- physical fidelity;
- statistical support;
- causal interpretation.

A SHA-256 identity only states which bytes or canonical JSON value is being
referenced. It is not a signature and does not establish origin, chronology,
correctness, or truth.

F3 will require an explicit trust model before signatures or provider receipts
are admitted. That design must specify signed bytes, key identity, revocation,
clock assumptions, replay handling, and what each attestation is permitted to
establish.
