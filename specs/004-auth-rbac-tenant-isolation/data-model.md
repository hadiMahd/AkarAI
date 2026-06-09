# Data Model: Auth, RBAC, and Tenant Isolation

## Conventions

- IDs are UUIDs.
- Mutable records include `created_at` and `updated_at`.
- Security records are retained for auditability; revocation/deactivation uses status fields rather than hard deletion.
- Phase 3 adds only security and tenant-isolation records. Listings, leads, scheduled viewings, RAG documents/chunks, media, dashboards, and agency business profile tables remain out of scope.

## Entities

### User

Purpose: Base actor identity for users, agency employees, and platform admins.

Fields:
- `id`
- `email`
- `password_hash`
- `name`
- `phone`
- `preferred_language`
- `role_id`
- `is_active`
- `status`: active, inactive, deactivated, suspended
- `last_login_at`
- `password_changed_at`
- `created_at`
- `updated_at`
- `deleted_at`

Relationships:
- Belongs to one Role.
- May have many RefreshSessions.
- May have many AgencyEmployeeMembership records.

Validation:
- Email is normalized and unique.
- Password verifier is required for actors using credential sign-in.
- Inactive, deactivated, suspended, or deleted actors cannot sign in or refresh.

State transitions:
- `active -> inactive`
- `active -> deactivated`
- `active -> suspended`
- any non-deleted state -> `deleted`

### Role

Purpose: Approved project role.

Fields:
- `id`
- `name`: User, Agency Admin, Support Employee, Platform Admin
- `slug`
- `scope`: user, agency, platform
- `description`
- `created_at`
- `updated_at`

Relationships:
- Has many RolePermission records.
- Has many Users.

Validation:
- Only approved role names are valid.
- Slug is unique.

### Permission

Purpose: Named capability required by protected actions.

Fields:
- `id`
- `key`
- `scope`: user, agency, platform, auth, system
- `description`
- `created_at`
- `updated_at`

Relationships:
- Has many RolePermission records.

Validation:
- Permission key is unique and stable.

### RolePermission

Purpose: Grant of a permission to a role.

Fields:
- `role_id`
- `permission_id`
- `created_at`

Relationships:
- Belongs to Role.
- Belongs to Permission.

Validation:
- A role-permission pair is unique.

### AgencyTenant

Purpose: Minimal agency tenant identity used for security isolation.

Fields:
- `id`
- `name`
- `slug`
- `status`: active, inactive, suspended
- `created_at`
- `updated_at`
- `deleted_at`

Relationships:
- Has many AgencyEmployeeMembership records.

Validation:
- Slug is unique.
- Suspended or inactive tenants cannot authorize agency-scoped actions.

State transitions:
- `active -> inactive`
- `active -> suspended`
- any non-deleted state -> `deleted`

### AgencyEmployeeMembership

Purpose: Security membership linking an actor to an agency tenant.

Fields:
- `id`
- `agency_tenant_id`
- `user_id`
- `role_id`
- `status`: active, deactivated
- `deactivated_at`
- `deactivated_by_user_id`
- `deactivation_reason`
- `created_at`
- `updated_at`

Relationships:
- Belongs to AgencyTenant.
- Belongs to User.
- Belongs to Role.
- Optionally references the actor that deactivated the membership.

Validation:
- Membership role must be Agency Admin or Support Employee.
- Active membership is required for agency-scoped access.
- Deactivation invalidates active sessions for that employee.

State transitions:
- `active -> deactivated`

### RefreshSession

Purpose: Persisted refresh session for rotation, revocation, and suspicious-session response.

Fields:
- `id`
- `user_id`
- `token_hash`
- `family_id`
- `issued_at`
- `expires_at`
- `last_used_at`
- `revoked_at`
- `revocation_reason`: logout, password_reset, employee_deactivation, suspicious_session, refresh_rotation, admin_revocation
- `replaced_by_session_id`
- `ip_address`
- `user_agent`
- `created_at`
- `updated_at`

Relationships:
- Belongs to User.
- May reference replacement RefreshSession.

Validation:
- Token hash is unique.
- Expired or revoked sessions cannot refresh access.
- Rotated sessions cannot be reused.

State transitions:
- `active -> rotated`
- `active -> revoked`
- `active -> expired`

### AccessRevocation

Purpose: Marker for invalidated access credential identifiers.

Fields:
- `id`
- `jti`
- `user_id`
- `reason`
- `expires_at`
- `created_at`

Relationships:
- Belongs to User.

Validation:
- `jti` is unique.
- Revocation marker remains until the original credential would have expired.

### TenantContext

Purpose: Runtime context attached to protected work.

Fields:
- `actor_id`
- `role`
- `permissions`
- `tenant_id`
- `membership_id`
- `is_platform_actor`

Validation:
- Tenant-scoped actions require a matching active tenant and membership.
- Platform-level actions require explicit platform permissions.
- Missing context fails closed.

### AuditEvent

Purpose: Security audit record for authentication, authorization, tenant, and revocation behavior.

Fields:
- `id`
- `request_id`
- `actor_user_id`
- `tenant_id`
- `action`
- `resource_type`
- `resource_id`
- `result`: success, failure, denied
- `metadata`
- `ip_address`
- `user_agent`
- `created_at`

Validation:
- Security outcomes append audit events.
- Audit records are not hard-deleted.

## Required Security Actions

- `auth.sign_in.success`
- `auth.sign_in.failure`
- `auth.refresh.success`
- `auth.refresh.failure`
- `auth.sign_out`
- `auth.password_reset`
- `auth.session_revoked`
- `auth.employee_deactivated`
- `auth.permission_denied`
- `auth.tenant_denied`
- `auth.rate_limited`
