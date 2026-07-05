---
id: 20240110-flaky-ci-timeouts
title: Flaky CI — integration tests time out under load
type: result
project: demo
date: 2024-01-10
status: done
milestone: false
keywords: [ci, flaky, timeout, contention]
---
## Motivation
Integration tests failed ~1 run in 8, always on the same three network-bound
cases. Needed the cause before adding blind retries.

## Guess -> Method -> Result
- Guess: a race in the code under test.
- Method: rerun the three cases in isolation vs. under full parallel load; log
  wall-clock per request.
- Result: passes in isolation, fails under load — the shared test runner
  saturates connections and requests exceed a fixed 2 s timeout. It is
  contention, not a product race.

## On-going
- [ ] pick a fix: raise timeout, cap parallelism, or retry with backoff

## Links
- part-of:: [[20240101-ci-reliability]]
- next:: [[20240112-retry-with-backoff]]
