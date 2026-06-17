# Quickstart: Lead Processing Pipeline

## Prerequisites
- Docker Compose stack running
- Backend, worker, and model service available
- Seed data with at least one agency and one listing

## Validate the Flow
1. Create a new lead from the user app.
2. Confirm the lead is stored before classification finishes.
3. Confirm the worker forwards the job to the lead model service.
4. Confirm the model service returns spam or non-spam first.
5. If the lead is non-spam, confirm Hot/Normal is assigned.
6. Open the agency lead list and confirm the classification result is visible.
7. Mark the lead reviewed and confirm the reviewed state persists.

## Expected Outcome
- Lead creation succeeds even while classification runs asynchronously.
- Spam leads are separated from normal leads.
- Non-spam leads receive a Hot/Normal result.
- Review state persists after refresh.

## Related Artifacts
- Data model: [data-model.md](./data-model.md)
- Spec: [spec.md](./spec.md)
