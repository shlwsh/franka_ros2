# v1-20260607-102334 RA-L Robot Video Plan

> Manuscript: `latex/main-ral.tex`
> Purpose: support RA-L multimedia submission without replacing the main paper evidence.

## Storyboard

| Segment | Duration | Content | Evidence linked in paper |
|---------|----------|---------|--------------------------|
| 1 | 10 s | FR3 moves to the tongue-imaging pose using named ROS 2 / MoveIt skill | System architecture |
| 2 | 15 s | Edge gateway scores a captured frame with Edge-IQA and displays blur/exposure flags | Edge-IQA method |
| 3 | 15 s | LangGraph route chooses upload / resample / fail-safe under retry budget | Routing method |
| 4 | 15 s | Resample action produces a second frame and logs JSONL timestamps | Closed-loop evidence |
| 5 | 10 s | Overlay Table II headline metrics and link to anonymized reproduction package | Experiments |

## Double-Anonymous Constraints

- Do not show faces, badges, lab name, institution logos, usernames, or repository owner names.
- Use anonymized terminal paths and repository URLs.
- Include only robot, monitor overlays, and anonymized logs.
- Keep the video supplementary; the main text must remain understandable without it.

## Deliverables

- `video-ral-v1-20260607-102334.mp4`
- `video-ral-v1-20260607-102334-captions.srt`
- `video-ral-v1-20260607-102334-readme.md`
