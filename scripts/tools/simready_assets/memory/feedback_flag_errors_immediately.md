---
name: Flag errors immediately
description: Always flag failing models/components to the user immediately, don't silently continue
type: feedback
---

Flag errors immediately — don't let failing models slide because other models compensate.

**Why:** SAM 3 and Depth Pro failed on every single run but I kept going because Gemini carried the pipeline. User only found out much later. The whole point of multi-model fusion is redundancy — if models are failing silently, the pipeline is weaker than it appears.

**How to apply:** When any AI model or critical component fails during a test run, immediately tell the user: "X is failing with this error, here's what I need to fix it." Don't bury it in output logs and move on.
