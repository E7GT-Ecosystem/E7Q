# Milestone 20 — OpenQASM 2 import and deterministic hardware assessment

E7Q 1.0.0-rc9 closes the two deliberate gaps left by the RC8 external evidence
importer: typed import of supplied OpenQASM 2.0 circuits and an
algorithm-specific deterministic-bit assessment.

The importer preserves supported circuit structure without allocating a state
vector or claiming general OpenQASM execution. The assessor requires embedded
counts, an explicit count-label order, named deterministic cases, primary bit
indices, a minimum probability, a confidence level and an exploratory or
prospective claim mode.

The QEC pilot's hardware profile makes syndrome bits primary, records data bits
separately, and checks the aggregate modal XOR and zero-syndrome relations. Its
first hardware application remains retrospective and exploratory.

This milestone does not add provider authentication, hardware submission,
physical fidelity, fault tolerance, decoder assessment or a new QEC theorem.
