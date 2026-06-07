# v1-20260607-102334 RA-L Anonymous Submission Checklist

| Check | Status | Evidence |
|-------|--------|----------|
| Author names removed from `main-ral.tex` | done | `\author{Anonymous Authors}` |
| Affiliation/email removed from manuscript | done | no `\thanks{...}` in `main-ral.tex` |
| Identifying acknowledgment omitted | done | `sections/ral/00_disclosures.tex` |
| AI/data/code statement retained without institution | done | `sections/ral/00_disclosures.tex` |
| Video plan avoids identity leakage | done | `video_plan.md` |
| Citation audit run | partial | `data/papers/cite_audit.json`: 11 cited, 6 with local PDF, 5 missing |
| PDF build | blocked | local TeX lacks `IEEEtran.cls` |
