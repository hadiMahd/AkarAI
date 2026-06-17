# Lead Processing API Contract

## Backend callback endpoint
- Receives lead model service results for spam and Hot/Normal classification.
- Must validate tenant, lead identity, stage order, and retry metadata.

## Lead creation event
- `lead.created` is emitted after the lead is saved.
- The worker consumes the event and forwards the job to the model service.
