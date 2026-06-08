# Paper II English Draft

## Knowledge-Graph-Gated Multi-Agent Embodied Conflict Realignment for Anti-Hallucination in Multimodal EHR Synthesis: A Reproducible Prototype Study

**Author**: Honglei Shi  
**Version**: 2026-05-31 MVP draft (74 pytest passing, 18-gate readiness audit)  
**Evidence sources**: `doctor/paper2/experiments/logs/paper2_run_001.jsonl`, `doctor/paper2/experiments/results/*.csv`  
**Important note**: This is a synthetic MVP manuscript. It does not use real clinical records, protected health information, external LLM calls, or restricted medical ontology dumps. The reported numbers demonstrate an executable research pipeline inside the project; they must not be presented as clinical validation results.

---

## Abstract

Multimodal electronic health record synthesis must reconcile unstructured symptom narratives, visual findings, knowledge-graph evidence, and structured interoperability constraints. When textual symptoms conflict with visual tags, image quality is insufficient, or structured resources miss required evidence fields, a linear generative workflow can produce unsupported clinical statements. We propose a knowledge-graph-gated multi-agent embodied closed-loop method for conflict realignment and anti-hallucination in multimodal EHR synthesis. Built on the existing `franka_ros2` edge API and embodied skill surface, the prototype connects a Symptom Agent, Vision Agent, KG Conflict Agent, Action Agent, and EMR/FHIR Agent through a shared state object. The system records symptom entities, visual tags, KG matches, conflict confidence, tool calls, and FHIR drafts. If the gate score is below a safety threshold, the state machine routes the workflow to resampling, follow-up questioning, KG query, FHIR repair, or human review instead of directly rendering the final note.

In the current MVP, we construct 24 synthetic trials and evaluate five baselines: B0 linear generation, B1 self-reflection, B2 KG-gated routing, B3 embodied closed loop, and B4 tool-enhanced closed loop. The run produces 120 JSONL audit records. B0 obtains a conflict-detection F1 of 0.7500 and a hallucination rate of 0.6250. With KG gating, B2 reaches an F1 of 1.0000 and reduces hallucination rate to 0.0000. B4 preserves an F1 of 1.0000 and improves the FHIR valid rate to 0.6250. We also add a dataset registry, CSV/JSONL case loader, no-PHI sample replay script, and trainable graph-attention-lite baseline for later controlled-data and GNN/GAT integration, without claiming that real public-dataset experiments or large-scale graph-neural training are complete. These results show that the prototype executes a traceable text/vision perception, KG conflict gating, tool invocation, and structured-output validation loop, providing an engineering foundation for future public-dataset experiments, formal FHIR validation, and graph-neural KG embeddings.

**Keywords**: multi-agent systems; knowledge graph; anti-hallucination; electronic health records; HL7 FHIR; embodied AI; ROS 2; Franka FR3

---

## 1. Introduction

Digital clinical rooms and embodied medical acquisition systems increasingly route images, speech, text, and robot state into a unified clinical information flow. Compared with unimodal documentation, multimodal EHR synthesis faces three additional failure modes. First, the chief complaint and visual findings may conflict. Second, image quality, occlusion, and acquisition pose can affect the reliability of visual tags. Third, a generative model may fill missing evidence with plausible but unsupported clinical statements.

The existing `franka_ros2` project has already established a Paper I closed loop for edge image quality assessment, confidence-aware routing, and FR3 resampling. Paper II extends this idea from image-quality routing to semantic conflict routing. The central question is whether a multi-agent state machine can interrupt hallucination-prone paths and redirect the workflow to resampling, follow-up questioning, retrieval, or repair when inconsistency spans text, vision, knowledge constraints, and structured EHR standards.

The contributions of this draft are:

1. A KG-gated multi-agent closed-loop architecture for multimodal EMR synthesis, integrating symptom extraction, visual quality assessment, KG conflict gating, embodied tool use, and FHIR validation.
2. A reproducible synthetic MVP under `doctor/paper2`, producing JSONL traces, CSV metrics, and a report.
3. Five baselines, B0-B4, that quantify the preliminary effect of KG gating and tool invocation on conflict detection, hallucination rate, and FHIR validity.
4. A clear engineering boundary: `franka_ros2` provides the ROS 2, MoveIt, FastAPI, and skill-based embodied tool layer, while medical reasoning experiments are kept in `doctor/paper2`.

---

## 2. Background and Standards

The prototype represents multi-agent control as a state graph. LangGraph documentation describes `StateGraph` as a graph abstraction over shared state, which is suitable for multi-step workflows with conditional edges. HL7 FHIR Bundle, Composition, and Observation resources provide interoperable representations for structured clinical documents and findings; in FHIR R4, a document Bundle starts with a Composition entry. Public controlled datasets such as MIMIC-IV, MIMIC-IV-Note, and MIMIC-CXR can support future EHR-text and imaging-report experiments, but they require PhysioNet credentialing, data-use compliance, and local ethics approval. Ontology resources such as SNOMED CT also require license-aware handling. Therefore, the current MVP uses only a small project-local KG stub and a placeholder-only entity map for ICD/SNOMED/FHIR alignment interfaces; it does not distribute restricted ontology content.

---

## 3. Methods

### 3.1 System Architecture

The system has three layers:

1. **Cognition/research layer**: `doctor/paper2`, containing the state machine, agents, KG stub, experiments, and manuscript evidence.
2. **Edge API layer**: `franka_api_server`, exposing `/api/v1/vision/evaluate`, `/api/v1/motion/skills/{skill_name}`, status endpoints, and WebSocket telemetry.
3. **Embodied execution layer**: existing `franka_*` ROS 2 packages for FR3, MoveIt, Gazebo, and ros2_control.

### 3.2 Shared State Object

`Paper2State` includes `trial_id`, `case_id`, `symptom_text`, `symptom_entities`, `q_img`, `vision_tags`, `kg_matches`, `gamma_conflict`, `route_decision`, `tool_calls`, `emr_draft`, `fhir_bundle`, `fhir_valid`, and `latency_ms`. Every trial is written to JSONL so that manuscript numbers are traceable to execution records.

### 3.3 Knowledge-Graph Gate

The KG Conflict Agent computes:

```text
gamma_conflict = 0.28 * entity_completeness
               + 0.24 * vision_quality
               + 0.36 * kg_consistency
               - 0.22 * contradiction_penalty
```

If the text lacks required entities, the image quality is low, or the KG contains contradiction edges, the state machine routes the case to `ask_followup`, `resample_vision`, `query_kg`, or `human_review` instead of directly generating the final EMR.

To advance the P2-2 graph experiment, we export `doctor/paper2/kg/kg_edges.csv`, implement a deterministic signed-edge propagation ablation, and add message-passing embedding and graph-attention-lite ablations. The embedding baseline initializes KG nodes with one-hot vectors, propagates signed messages over support and contradiction edges, and scores text-vision compatibility by cosine similarity between pooled text-entity and vision-tag embeddings. The graph-attention-lite baseline learns support-edge, contradiction-edge, low-quality-image, and missing-entity attention weights from KG edges and synthetic replay labels. This is not full large-scale neural GNN training, but it moves the JSON KG stub into an auditable edge table, reproducible embedding score, and dependency-light trainable graph baseline.

To advance P2-KG-2, we add `doctor/paper2/kg/entity_map.csv` and `doctor/paper2/kg/entity_map_coverage.py`. The map covers symptom and visual-finding entities from the KG stub and records project-local codes, FHIR targets, ICD/SNOMED placeholders, and license status. It fixes schema and coverage accounting only; it does not include real restricted ICD/SNOMED/UMLS ontology text. `ONTOLOGY_LICENSE_NOTES.md` documents the constraints before replacing placeholders with licensed identifiers.

### 3.4 Tool Invocation and Embodied Resampling

The Action Agent currently implements three tools: `execute_skill`, `ask_followup`, and `query_kg`. In B3 and B4, low-quality visual cases trigger the synthetic `go_to_tongue_pose` resampling tool, simulating an FR3 pose adjustment that improves image quality. Future real-robot experiments should call named skills only; the research layer must not send raw joint commands.

### 3.5 EMR/FHIR Generation and Repair

The EMR/FHIR Agent generates a minimal document Bundle containing Composition, Patient, and Observation resources. The first entry must be a Composition, and both Composition and Observation must carry a Patient subject reference. If Observation is missing, B4 may call `repair_fhir`, add the missing resource, and validate again. The system now includes `doctor/paper2/tools/fhir_validator.py`: it uses local structural validation by default, can call an external FHIR validator CLI through `PAPER2_FHIR_VALIDATOR_CMD`, and records the validation mode in JSONL. To make validation evidence replayable, `doctor/paper2/experiments/run_fhir_validation_replay.py` exports each trial Bundle as JSON and writes a batch validator replay CSV/report over the same artifacts; an official external validator can be wired to the same exported files later.

To advance the P2-3 edge-tool integration, we also provide `doctor/paper2/tools/franka_probe.py`. The probe checks whether `franka_api_server` exposes `/status/joints` and `/motion/skills`, returning `online`, `partial`, or `offline` without making the synthetic MVP fail when ROS or the API server is unavailable.

### 3.6 Dataset Registry and Replay Bridge

To advance the P2-5 public/controlled dataset experiment, we add `doctor/paper2/datasets/registry.json`, `doctor/paper2/tools/dataset_loader.py`, and `doctor/paper2/experiments/run_dataset_replay.py`. The registry separates open, controlled, and restricted sources and records license, access level, source type, and local derived-path placeholders. The tracked `sample_open_csv` entry is a project-local no-PHI synthetic fixture. The `mimic_iv_note_placeholder` and `mimic_cxr_placeholder` entries record controlled-data metadata only; they do not include source records, images, or reports. The loader supports CSV, JSONL, and JSON and validates fields such as `case_id`, `symptom_text`, `expected_entities`, `vision_tags`, `q_img`, and `conflict_label`. Controlled entries fail unless `allow_controlled` is explicitly enabled and a local derived file exists, reducing the risk of accidentally committing unauthorized clinical data.

---

## 4. Experimental Design

### 4.1 Data and Task

The experiment expands eight synthetic case templates into 24 trials. Each case contains a chief complaint, expected entities, visual tags, an image-quality score, a conflict label, and an FHIR-missing marker. Conflict types include low visual quality, missing text entities, text-vision contradiction, and missing FHIR fields. We also run the `sample_open_csv` no-PHI fixture through the dataset replay bridge to verify registry loading, file parsing, B0-B4 replay, and result export.

### 4.2 Baselines

| Baseline | Name | Description |
|---|---|---|
| B0 | Linear EMR | Direct EMR/FHIR generation without gating |
| B1 | Self-Reflection | Shallow routing using image quality and text completeness |
| B2 | KG-Gated | KG conflict gating without embodied resampling |
| B3 | Embodied Closed Loop | KG gating plus embodied resampling tools |
| B4 | Tool-Enhanced Closed Loop | B3 plus FHIR repair and stricter review routing |

### 4.3 Metrics

Metrics include conflict-detection precision, recall and F1, hallucination rate, FHIR valid rate, average closed-loop latency, and tool-call rate. The evidence file is `doctor/paper2/experiments/results/paper2_summary.csv`. Figures are generated from CSV by `doctor/paper2/figures/plot_results.py` to prevent manual number drift.

---

## 5. Results

| Baseline | Precision | Recall | F1 | Hallucination Rate | FHIR Valid Rate | Tool Call Rate |
|---|---:|---:|---:|---:|---:|---:|
| B0 | 1.0000 | 0.6000 | 0.7500 | 0.6250 | 0.7500 | 0.0000 |
| B1 | 1.0000 | 1.0000 | 1.0000 | 0.2500 | 0.5000 | 0.1250 |
| B2 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.2500 | 0.3750 |
| B3 | 1.0000 | 1.0000 | 1.0000 | 0.2500 | 0.3750 | 0.6250 |
| B4 | 1.0000 | 1.0000 | 1.0000 | 0.2500 | 0.6250 | 0.6250 |

B0 reaches only 0.6000 recall for conflict cases, indicating that a linear workflow misses low-quality vision cases and text-vision contradictions, resulting in a hallucination rate of 0.6250. B2 reduces the hallucination rate to 0.0000 through KG gating, but its conservative review behavior leaves the FHIR valid rate at 0.2500. B4 improves the FHIR valid rate to 0.6250 with a tool-call rate of 0.6250, indicating that the FHIR repair tool directly contributes to structured-output validity.

The generated figures are `doctor/paper2/figures/paper2_summary_metrics.svg` and `doctor/paper2/figures/paper2_hallucination_fhir_tradeoff.svg`. The first summarizes F1, hallucination rate, FHIR valid rate, and tool-call rate, while the second visualizes the hallucination-FHIR validity trade-off. Both figures are generated directly from CSV outputs.

The KG propagation ablation generates `doctor/paper2/experiments/results/kg_propagation.csv` and `doctor/paper2/experiments/reports/kg_propagation_report.md`. On 24 synthetic trials, signed-edge propagation obtains precision, recall, and F1 of 1.0000 for conflict detection. The corresponding figure is `doctor/paper2/figures/paper2_kg_propagation_scores.svg`.

The entity-map coverage report generates `doctor/paper2/experiments/results/entity_map_coverage.csv` and `doctor/paper2/experiments/reports/entity_map_coverage_report.md`. At this stage, 10/10 KG entities have project-local mappings, giving coverage 1.0000; FHIR target coverage is also 1.0000; all ICD/SNOMED fields remain `placeholder-only`. The corresponding figure is `doctor/paper2/figures/paper2_entity_map_coverage.svg`. To prepare for licensed ontology replacement, `run_ontology_identifier_audit.py` now writes `licensed_ontology_identifiers.template.csv` and validates future mapping evidence for complete KG-entity coverage, license approval, approval evidence URI, source release metadata, artifact SHA-256, and absence of restricted ontology text in the repository. The default audit remains blocked because no real `licensed_ontology_identifiers.csv` exists.

The message-passing embedding ablation generates `doctor/paper2/experiments/results/graph_embedding.csv` and `doctor/paper2/experiments/reports/graph_embedding_report.md`. On the same 24 synthetic trials, it obtains precision, recall, and F1 of 1.0000 for conflict detection. The corresponding figure is `doctor/paper2/figures/paper2_graph_embedding_scores.svg`.

The trainable graph-attention-lite ablation generates `doctor/paper2/experiments/results/graph_attention.csv` and `doctor/paper2/experiments/reports/graph_attention_report.md`. On the same 24 synthetic trials, it obtains precision, recall, and F1 of 1.0000 for conflict detection. The learned support attention is -7.7959, contradiction attention is 6.1827, and low-quality attention is 14.9607. The corresponding figure is `doctor/paper2/figures/paper2_graph_attention_scores.svg`. To prevent this small baseline from being mistaken for the required large graph experiment, `run_large_gnn_evidence_audit.py` now writes a `large_gnn_evidence.template.csv` and validates future evidence for license approval, non-placeholder ontology identifiers, graph scale, model family, data splits, metric values, evidence URI, and artifact SHA-256. In the default run the large-GNN audit remains blocked because no real `large_gnn_evidence.csv` exists.

The FHIR validator replay generates `doctor/paper2/experiments/results/fhir_validator_replay.csv`, `doctor/paper2/experiments/reports/fhir_validator_replay_report.md`, and exported Bundle JSON files under `doctor/paper2/experiments/fhir_bundles/`. It exports 120 Bundle JSON artifacts and validates them in `local-structural` mode. B0-B3 each obtain a Bundle valid rate of 0.7500, while B4 obtains 1.0000. The corresponding figure is `doctor/paper2/figures/paper2_fhir_validator_replay.svg`. A separate official-validator audit script writes `official_fhir_validator_audit.csv` and records the validator command, validator artifact SHA-256, local-valid external passes, and unexpected rejects. In the default offline run this audit is blocked because no official validator command or jar artifact is configured.

These results are internal validity evidence for the synthetic MVP. They do not establish generalization to real clinical settings. Future work must use public datasets, official FHIR validation, and human evaluation protocols.

The dataset replay experiment generates `doctor/paper2/experiments/results/dataset_replay.csv` and `doctor/paper2/experiments/reports/dataset_replay_report.md`. In a 24-trial replay on the `sample_open_csv` fixture, B0 obtains F1 0.8000, hallucination rate 0.5000, and FHIR valid rate 0.8333, while B4 obtains F1 1.0000, hallucination rate 0.1667, and FHIR valid rate 0.6667. The corresponding figure is `doctor/paper2/figures/paper2_dataset_replay_rates.svg`. This experiment validates the engineering bridge only; it is not a real public-dataset conclusion.

To prepare for real public or controlled main experiments, we add `doctor/paper2/experiments/run_dataset_compliance_audit.py`. Without copying source clinical records into the repository, the script audits registry metadata, derived case-file schema, whether controlled-data paths stay outside the repository, lightweight PHI-like patterns, and approval-evidence fields. The current dataset compliance audit reports four registry entries: two software fixtures are ready and two controlled placeholders are blocked; required real dataset readiness is 0/2, so `submission-dataset-ready` is `no`. The audit generates `doctor/paper2/experiments/results/dataset_compliance_audit.csv`, `doctor/paper2/experiments/reports/dataset_compliance_audit_report.md`, and `doctor/paper2/figures/paper2_dataset_compliance_audit.svg`.

The expert review protocol validation generates `doctor/paper2/experiments/expert_review/PROTOCOL.md`, `doctor/paper2/experiments/expert_review/review_packet.csv`, `doctor/paper2/experiments/expert_review/synthetic_annotations.csv`, and `doctor/paper2/experiments/results/expert_review_agreement.csv`. The current packet contains 40 review items and 80 placeholder annotations from two synthetic reviewers. Cohen kappa is 1.0000 for `factually_supported` and `fhir_acceptable`, and 0.8961 for `needs_human_review`. The corresponding figure is `doctor/paper2/figures/paper2_expert_review_agreement.svg`. This validates the blinded review schema and agreement script only; it is not real expert review.

To prepare for real expert review, we add `doctor/paper2/experiments/run_real_expert_review.py`. The script does not synthesize real labels. It writes a `real_annotations.template.csv` from the current review packet, then validates a completed `real_annotations.csv` by requiring at least two non-synthetic reviewers, item IDs that match the review packet, at least two reviewers per item, valid boolean fields, and an `overall_score` in the range 1-5. Only a validated real annotation file can generate `real_expert_review_agreement.csv` and `real_expert_review_report.md`, and the readiness audit accepts real expert review only through the same validation path.

To prepare for real Gazebo/FR3 embodied closed-loop evidence, we add `doctor/paper2/experiments/run_franka_closed_loop.py`. The script requires an online `franka_api_server`, probes `/status/joints` and `/motion/skills`, executes named skills through HTTP, and records `probe_status`, `skill_success`, `latency_ms`, `joints_ok`, and `skills_ok` in `franka_closed_loop.csv`. The readiness audit validates these fields instead of accepting a CSV file by existence alone. The default offline reproduction does not connect to fake hardware, Gazebo, or FR3, so this gate remains blocked.

To keep the Chinese and English manuscripts synchronized, we add a bilingual manuscript sync audit, `doctor/paper2/experiments/run_bilingual_sync_audit.py`. The script does not attempt automatic translation. Instead, it mechanically checks the Chinese Markdown, English Markdown, Chinese LaTeX, English LaTeX, and paired PDFs for the same key evidence: synthetic MVP scope, B0/B2/B4 metrics, dataset replay, dataset compliance audit, placeholder-only entity map, licensed-ontology identifier audit, large-GNN/GAT evidence audit, FHIR replay, official-validator audit, real expert-review template, Franka API/Gazebo/FR3 collector, closed_loop_summary latency summary, phase_completion_audit phase completion audit, readiness counts, and `submission-ready = no`. The audit generates `doctor/paper2/experiments/results/bilingual_sync_audit.csv` and `doctor/paper2/experiments/reports/bilingual_sync_audit_report.md`.

The M6-style closed-loop latency summary is generated by `doctor/paper2/experiments/summarize_closed_loop.py`. For the current 120 synthetic local trials, the overall latency p50 is 0.0420 ms, p95 is 0.0771 ms, the tool-call rate is 0.3500, and both initial and final route distributions are recorded. This result reflects the local software path only, not measured Gazebo/FR3 RTT.

To avoid presenting the software prototype as submission-ready evidence, we add a readiness audit. `doctor/paper2/experiments/run_readiness_audit.py` conservatively gates datasets, licensed ontology identifiers, official FHIR validation, Franka API/Gazebo/FR3 closed-loop evidence, large-graph GNN/GAT evidence, expert review, bilingual manuscript artifacts, bilingual_sync_audit content synchronization, and phase_completion_audit phase completion. In the default offline reproduction mode, 7 of 18 gates are ready, 1 is partial, and 10 are blocked; 3 of 13 submission-required gates are ready, so `submission-ready` is `no`. The phase_completion_audit covers 35 planned phase tasks: 23 are ready, 11 are partial, and 1 is blocked; no submission-required phase task is blocked. The audit generates `doctor/paper2/experiments/results/readiness_audit.csv`, `doctor/paper2/experiments/reports/readiness_audit_report.md`, `doctor/paper2/experiments/results/phase_completion_audit.csv`, `doctor/paper2/experiments/reports/phase_completion_audit_report.md`, and `doctor/paper2/figures/paper2_readiness_audit.svg`.

---

## 6. Discussion

The prototype shows that the image-quality routing idea from Paper I can be extended to multimodal semantic conflict routing for Paper II. The critical design choice is not to ask an LLM to decide everything in one step, but to preserve evidence, conflict scores, and tool calls explicitly in a state machine. When context is incomplete or modalities disagree, the system produces auditable intermediate behavior instead of hiding uncertainty in the final generated note.

The MVP has important limitations. The data are synthetic and cannot support clinical claims; the new dataset replay layer and compliance audit are only an engineering base for later public/controlled data. The KG is a small rule table, the entity map remains placeholder-only, and graph-attention-lite is not an ICD/SNOMED-scale graph model; a large-GNN evidence audit template exists, but no real licensed large-graph training evidence has passed it. FHIR replay still uses the local structural checker by default; although the external CLI interface, batch Bundle export, and official-validator audit gate are in place, an official validator jar has not yet been run. Expert review is currently a synthetic protocol validation; although a real annotation template and validator are now available, real clinicians have not yet completed the review. The resampling action is synthetic; although a Franka API/Gazebo/FR3 evidence collector and validator are now available, no live API has been connected in the default reproduction. Finally, bilingual_sync_audit only proves that both language versions cover the same key evidence; it does not replace human language polishing or journal-format review. The readiness audit makes these limitations explicit as blocked gates, so this manuscript should be treated as a reproducible MVP draft rather than a final clinical or submission-ready conclusion.

---

## 7. Conclusion

This work completes the first executable Paper II research prototype and bilingual manuscript evidence baseline. In synthetic settings, explicit KG gating and tool invocation convert missed conflicts in linear generation into auditable routing decisions and provide stronger factual constraints for EMR/FHIR synthesis. The next stage should focus on public datasets, official FHIR validator replay, licensed-ontology GNN/GAT training, real API/robot closed-loop execution, and real expert review.

---

## Data and Code Availability

The code is located in `doctor/paper2`. Run:

```bash
python3 -m doctor.paper2.langgraph_router.run --trials 24
python3 doctor/paper2/experiments/run_dataset_replay.py --trials 24 --dataset-id sample_open_csv
python3 doctor/paper2/experiments/run_fhir_validation_replay.py --trials 24
python3 doctor/paper2/experiments/run_official_fhir_validator_audit.py
python3 doctor/paper2/experiments/run_expert_review.py
```

to regenerate JSONL traces, CSV metrics, and the MVP report. The repository does not include real clinical data, PHI, or restricted ontology dumps.

---

## References and Standards

1. LangChain/LangGraph documentation. LangGraph overview and StateGraph reference. https://docs.langchain.com/oss/python/langgraph ; https://reference.langchain.com/python/langgraph/graph/state/StateGraph
2. HL7 FHIR R4 Bundle resource. https://hl7.org/fhir/R4/bundle.html
3. HL7 FHIR Observation resource. https://www.hl7.org/fhir/observation.html
4. HL7 FHIR Composition resource. https://hl7.org/fhir/composition.html
5. PhysioNet MIMIC-IV dataset documentation. https://physionet.org/content/mimiciv/3.1/
6. PhysioNet MIMIC-IV-Note dataset documentation. https://physionet.org/content/mimic-iv-note/
7. PhysioNet MIMIC-CXR dataset documentation. https://physionet.org/content/mimic-cxr/
8. PhysioNet credentialed access guidance. https://physionet.org/settings/credentialing/
9. U.S. National Library of Medicine SNOMED CT browser guidance. https://www.nlm.nih.gov/research/umls/Snomed/snomed_browsers.html
