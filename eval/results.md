# Agent evaluation results

- **Model:** `mistral-small-latest`
- **Methodology:** 5 runs per case per mode (150 total requests). Results reported as success rates to account for documented model non-determinism in timestamp formatting.
- **Citation validation:** Accepts both single `[MM:SS]` and range `[MM:SS - MM:SS]` formats. Validated against evidence segment start times.
- **Run ID:** `eval-1788167482`
- **Errors:** 0/150 requests failed.

## Per-case citation success rates

| Case | baseline cited | loop cited | orchestrated cited | baseline avg tools | loop avg tools | orchestrated avg tools |
|---|---:|---:|---:|---:|---:|---:|
| gravity-definition | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 1.0 | 1.0 | 2.0 |
| gravity-moon | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 1.0 | 1.0 | 1.0 |
| gravity-location | 0/5 (0%) | 4/5 (80%) | 5/5 (100%) | 1.0 | 1.6 | 1.4 |
| gravity-multipart | 0/5 (0%) | 2/5 (40%) | 5/5 (100%) | 1.0 | 2.0 | 4.6 |
| gravity-memory-setup | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 1.0 | 1.0 | 1.0 |
| gravity-memory-followup | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 1.0 | 1.2 | 1.4 |
| pyramid-scale | 1/5 (20%) | 2/5 (40%) | 1/5 (20%) | 1.0 | 3.6 | 3.8 |
| pyramid-location | 0/5 (0%) | 4/5 (80%) | 4/5 (80%) | 1.0 | 1.4 | 1.4 |
| pythagoras-use | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 1.0 | 1.4 | 1.4 |
| pythagoras-method | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 1.0 | 1.0 | 3.0 |

## Aggregate summary

- **baseline:** 31/50 cited (62% mean success rate); 50 total tool calls; follow-up 5/5; degraded 0/50.
- **loop:** 42/50 cited (84% mean success rate); 76 total tool calls; follow-up 5/5; degraded 0/50.
- **orchestrated:** 44/50 cited (88% mean success rate); 105 total tool calls; follow-up 5/5; degraded 0/50.

## Methodology notes

Each of the 10 cases was run 5 times per mode to measure variance.
Documented source of non-determinism: `mistral-small-latest` occasionally converts
sub-minute evidence timestamps (e.g. 5.44s) as `[05:00]` instead of `[00:05]`,
producing ~20% run-to-run citation failures on affected cases.
Single-run pass/fail snapshots were unreliable — this multi-run methodology replaces
them as the primary evidence.

