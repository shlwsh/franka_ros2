# Paper II Expert Review Protocol

This protocol defines the blinded annotation packet for future real expert review.
The tracked synthetic annotations are placeholders for software validation only.

## Reviewer Tasks

1. Mark whether the generated EMR/FHIR evidence is factually supported.
2. Mark whether the case should be routed to human review.
3. Mark whether the FHIR output is acceptable for structural interoperability review.
4. Assign an overall 1-5 confidence score.

## Safety and Data Rules

- Do not include PHI or source clinical records in the packet.
- Keep reviewer identities pseudonymous in analysis files.
- Report Cohen kappa and agreement rate for binary fields.
