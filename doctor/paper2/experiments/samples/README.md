# Paper II Samples

This directory stores small reviewable samples derived from generated JSONL
traces. Full logs are generated under `doctor/paper2/experiments/logs/`, which
is ignored by the repository-level `logs/` pattern.

Regenerate full evidence:

```bash
python3 -m doctor.paper2.langgraph_router.run --trials 24
```
