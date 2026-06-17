# Research: Lead Processing Pipeline

## Decision: Use a Separate Model Service Behind the Worker Pipeline
- **Decision**: The worker forwards `lead.created` jobs to a dedicated lead model service, and the model service calls back the backend with results.
- **Rationale**: This keeps inference scalable and isolates model runtime dependencies from the main API.
- **Alternatives considered**: Run models inline in the backend, or make the worker host the models directly.

## Decision: Use Callback Delivery for Model Results
- **Decision**: The model service posts results back to a backend callback endpoint.
- **Rationale**: Simpler than adding a second queue consumer path while still keeping the inference service independently scalable.
- **Alternatives considered**: Queue-based result consumption, synchronous worker response handling.

## Decision: Use the Existing Lead Event and Review Records as the Persistence Backbone
- **Decision**: Keep `lead.created`, spam results, Hot/Normal results, and reviewed lead records in PostgreSQL through the existing lead module.
- **Rationale**: The lead module already owns the domain records and tenant scoping.
- **Alternatives considered**: Create a new feature module or store processing state in Redis only.

## Decision: Retry Each Stage Three Times Before Falling Back
- **Decision**: Retry spam detection and Hot/Normal ranking up to three times each.
- **Rationale**: This balances resilience and predictable latency.
- **Alternatives considered**: Unlimited retries, single attempt only.

## Decision: Fail Open to Non-Spam / Normal After Exhausting Retries
- **Decision**: If spam detection and the downstream Hot/Normal stage both fail after retries, classify the lead as non-spam and normal rather than blocking lead creation.
- **Rationale**: Lead capture must not fail closed and lose customer inquiries.
- **Alternatives considered**: Leave the lead pending, reject the lead, or surface a hard failure.

## Decision: Store Models in a Dedicated Service Folder
- **Decision**: Move model runtime code and assets into the dedicated model service structure rather than leaving them as a loose `dump/` dependency.
- **Rationale**: It makes deployment and ownership clearer while preserving the local files as the seed artifacts.
- **Alternatives considered**: Keep using `dump/` directly at runtime.
