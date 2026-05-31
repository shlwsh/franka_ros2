# Paper II Ontology Mapping Notes

This repository tracks only project-local entity identifiers and placeholder
standard namespaces. It does not include ICD-11, SNOMED CT, UMLS, or other
restricted ontology dumps.

`entity_map.csv` is intentionally limited to:

- project entity names already present in `kg_stub.json`;
- project-local codes such as `P2SYM001`;
- intended FHIR resource targets;
- placeholder standard namespaces such as `ICD11_PLACEHOLDER` and
  `SNOMED_PLACEHOLDER`;
- license status notes.

Before replacing placeholders with real ontology identifiers, confirm the
license terms and keep raw ontology exports outside the repository. Commit only
derived mapping scripts, aggregate coverage metrics, and no-PHI review samples.
