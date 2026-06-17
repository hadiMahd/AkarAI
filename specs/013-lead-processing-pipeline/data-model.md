# Data Model: Lead Processing Pipeline

## Lead
- **Purpose**: A user inquiry submitted to an agency.
- **Key fields**: id, agency_tenant_id, listing_id, user_id, status, name, email, phone, message, source, created_at, updated_at, closed_at.
- **Relationships**: Belongs to one agency tenant and one listing; can have one spam result, one Hot/Normal result, and one reviewed record.

## LeadSpamResult
- **Purpose**: Records whether the lead was spam or not spam.
- **Key fields**: id, lead_id, agency_tenant_id, status, label, score, details, created_at, updated_at.
- **State**: pending -> completed/failed.

## LeadLevelResult
- **Purpose**: Records the Hot/Normal ranking for non-spam leads.
- **Key fields**: id, lead_id, agency_tenant_id, status, level, score, details, created_at, updated_at.
- **State**: pending -> completed/failed.

## ReviewedLeadRecord
- **Purpose**: Stores a support review action.
- **Key fields**: id, lead_id, agency_tenant_id, reviewed_by_user_id, outcome, notes, created_at.
- **Relationships**: References the lead and the user who reviewed it.

## LeadCreatedEvent
- **Purpose**: Durable domain event for new lead creation.
- **Key fields**: event_name, aggregate_type, aggregate_id, agency_tenant_id, actor_user_id, payload, created_at.
- **Usage**: Triggers the worker pipeline.

## LeadModelService Callback
- **Purpose**: External result handoff from the model service back to the backend.
- **Key fields**: lead_id, tenant_id, stage, result, score, details, retry_count, status.
- **Validation**: Tenant must match the stored lead and stage order must be preserved.
