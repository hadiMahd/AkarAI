# Implementation Plan: Semantic Cache

**Branch**: `[extra/004-semantic-cache]`

## Summary

Add semantic caching only after retrieval and generation quality is stable. The cache will be Redis-backed, vector-aware, and clearly separated from transactional source-of-truth reads.

## Scope

- cache AI retrieval or response outputs where repeated semantic similarity justifies it
- use Redis-backed vector similarity lookup
- define TTL, invalidation, cache versioning, and bypass rules
- keep cache misses and bypasses observable for debugging and eval work

## Non-Goals

- no caching of listings, leads, viewings, profile truth, or other transactional DB records
- no hiding of retrieval/generation regressions behind cached answers
- no coupling between semantic cache and authoritative domain writes

## Branch Outcome

This branch should add an optimization layer, not a correctness dependency.
