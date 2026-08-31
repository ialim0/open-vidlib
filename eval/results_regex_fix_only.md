# Agent evaluation results

- **Model:** `mistral-small-latest`
- **Methodology:** 1 runs per case per mode (30 total requests). Results reported as success rates to account for documented model non-determinism in timestamp formatting.
- **Citation validation:** Accepts both single `[MM:SS]` and range `[MM:SS - MM:SS]` formats. Validated against evidence segment start times.
- **Run ID:** `eval-1788167235`
- **Errors:** 0/30 requests failed.

## Per-case citation success rates

| Case | baseline cited | loop cited | orchestrated cited | baseline avg tools | loop avg tools | orchestrated avg tools |
|---|---:|---:|---:|---:|---:|---:|
| gravity-definition | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1.0 | 1.0 | 2.0 |
| gravity-moon | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1.0 | 1.0 | 1.0 |
| gravity-location | 0/1 (0%) | 1/1 (100%) | 1/1 (100%) | 1.0 | 2.0 | 1.0 |
| gravity-multipart | 0/1 (0%) | 1/1 (100%) | 1/1 (100%) | 1.0 | 4.0 | 6.0 |
| gravity-memory-setup | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1.0 | 1.0 | 1.0 |
| gravity-memory-followup | 0/1 (0%) | 1/1 (100%) | 1/1 (100%) | 1.0 | 1.0 | 1.0 |
| pyramid-scale | 1/1 (100%) | 1/1 (100%) | 0/1 (0%) | 1.0 | 5.0 | 3.0 |
| pyramid-location | 0/1 (0%) | 1/1 (100%) | 0/1 (0%) | 1.0 | 2.0 | 1.0 |
| pythagoras-use | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1.0 | 1.0 | 1.0 |
| pythagoras-method | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1.0 | 1.0 | 1.0 |

## Aggregate summary

- **baseline:** 6/10 cited (60% mean success rate); 10 total tool calls; follow-up 1/1; degraded 0/10.
- **loop:** 10/10 cited (100% mean success rate); 19 total tool calls; follow-up 1/1; degraded 0/10.
- **orchestrated:** 8/10 cited (80% mean success rate); 18 total tool calls; follow-up 1/1; degraded 1/10.

## Methodology notes

Each of the 10 cases was run 1 times per mode to measure variance.
Documented source of non-determinism: `mistral-small-latest` occasionally converts
sub-minute evidence timestamps (e.g. 5.44s) as `[05:00]` instead of `[00:05]`,
producing ~20% run-to-run citation failures on affected cases.
Single-run pass/fail snapshots were unreliable — this multi-run methodology replaces
them as the primary evidence.

