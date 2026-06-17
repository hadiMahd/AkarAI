# Tasks: Semantic Cache

- [ ] Define the semantic cache boundary and list the exact AI/retrieval paths eligible for caching.
- [ ] Add Redis-backed vector similarity lookup for cache retrieval.
- [ ] Add TTL, similarity threshold, cache version, and invalidation rules.
- [ ] Ensure cache bypass for eval/debug paths and for cases where fresh generation is required.
- [ ] Add observability for hit rate, miss rate, invalidations, and stale/bypass reasons.
- [ ] Add focused tests for hit/miss behavior, invalidation after source changes, and proof that source-of-truth DB reads are unaffected.
