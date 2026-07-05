---
id: 20240112-retry-with-backoff
title: Exponential backoff on the network-bound test client
type: method
project: demo
date: 2024-01-12
status: done
milestone: false
keywords: [retry, backoff, jitter, resilience]
---
## Motivation
Contention (not a race) caused the flaky timeouts, so retries are legitimate —
but naive retries thundering-herd the saturated runner.

## Guess -> Method -> Result
- Guess: bounded exponential backoff with jitter smooths the load spikes.
- Method: wrap the test client in retry with base 100 ms, factor 2, full
  jitter, cap 5 attempts; keep the 2 s per-attempt timeout.
- Result: the three cases pass reliably; suite-level flakiness drops toward
  zero over a week of runs.

## Links
- part-of:: [[20240101-ci-reliability]]
- motivates:: [[20240110-flaky-ci-timeouts]]
- next:: [[20240115-ci-green-1000-runs]]
