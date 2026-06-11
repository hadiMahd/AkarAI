# Agency Dashboard Route Contract

## Purpose

This contract defines the Phase 6 agency-app route map, role access rules, and the backend endpoint bindings each page depends on.

## Route Map

| Route | Audience | Purpose | Backend Contract |
|---|---|---|---|
| `/sign-in` | Public agency staff | Auth entry for agency admins and support employees | Existing auth login, refresh, logout, me |
| `/dashboard` | Agency admin, support employee | Summary cards and role-aware navigation shell | Existing totals from listings, leads, reviewed leads, and viewings endpoints |
| `/profile` | Agency admin only | Edit agency profile settings | `GET /agencies/me/profile`, `PUT /agencies/me/profile` |
| `/employees` | Agency admin only | List and manage support employees | `GET /agencies/me/employees`, `POST /agencies/me/employees`, `PATCH /agencies/me/employees/{employee_id}`, `DELETE /agencies/me/employees/{employee_id}` |
| `/listings` | Agency admin only | View the tenant listing table and open create/edit flows | `GET /agency/listings` |
| `/listings/new` | Agency admin only | Create a listing and publish immediately | `POST /agency/listings` with `status=active` |
| `/listings/:listingId` | Agency admin only | Review and edit a single listing | `GET /agency/listings/{listing_id}`, `PATCH /agency/listings/{listing_id}`, `DELETE /agency/listings/{listing_id}` |
| `/listings/:listingId/slots` | Agency admin only | Manage viewing slots for a listing | `GET/POST/PATCH/DELETE /agency/listings/{listing_id}/viewing-slots...` |
| `/leads` | Agency admin, support employee | Active leads queue | `GET /agency/leads?reviewed=false` |
| `/leads/reviewed` | Agency admin, support employee | Reviewed leads list | `GET /agency/leads?status=reviewed` |
| `/leads/:leadId` | Agency admin, support employee | Review a lead and mark it reviewed | `GET /agency/leads/{lead_id}`, `POST /agency/leads/{lead_id}/review` |
| `/viewings` | Agency admin, support employee | View scheduled viewings and filter them | `GET /agency/viewings?status=&listing_id=&date_from=&date_to=` |
| `/spam-leads` | Agency admin, support employee | Placeholder-only page for later spam workflow | No active API calls required |
| `/policy-documents` | Agency admin only | Placeholder-only page for later policy ingestion flow | No active API calls required |

## Role Rules

### Agency Admin

- Can view every Phase 6 route.
- Can update agency profile.
- Can add existing support employees by email.
- Can create, edit, publish, and archive listings.
- Can create, edit, and deactivate viewing slots.
- Can review leads.
- Can view scheduled viewings.

### Support Employee

- Can view `/dashboard`, `/leads`, `/leads/reviewed`, `/leads/:leadId`, and `/viewings`.
- Can mark leads as reviewed.
- Can only view schedules; schedule mutation controls are hidden and backend schedule-mutation requests must be rejected with `403`.
- Cannot access `/profile`, `/employees`, `/listings/new`, `/listings/:listingId/slots`, or employee-management actions.

## Employee Onboarding Contract Adjustment

Phase 6 requires an email-entry employee flow, while the current backend employee-create request is ID-based. The implementation should adjust the create contract to accept an email-based payload for support-employee onboarding against existing user accounts.

### Request

`POST /agencies/me/employees`

```json
{
  "work_email": "support.new@agency.test",
  "display_name": "New Support Employee",
  "role_slug": "support_employee"
}
```

### Expected Behavior

- The backend resolves the target user account by email.
- If the account exists and is not already a member of the tenant, a support-employee membership is created.
- If the account does not exist, the API returns a clear validation or business-rule error.
- No outbound email delivery is triggered in this phase.

### Response

- `201 Created` with the updated employee row using the existing employee response shape.
- Clear failure states for duplicate membership, missing user account, or forbidden role assignment.

## Viewing Schedule Filter Contract

`GET /agency/viewings`

Supported query params:

- `page`
- `page_size`
- `status` - optional scheduled-viewing status value
- `listing_id` - optional UUID of one tenant-owned listing
- `date_from` - optional ISO date lower bound applied to scheduled start time
- `date_to` - optional ISO date upper bound applied to scheduled start time

Expected behavior:

- Filters can be combined.
- Empty matches return `200` with an empty paginated response.
- Support employees can call the filtered list endpoint.
- Schedule-status mutation remains admin-only through `PATCH /agency/viewings/{viewing_id}`.

## Dashboard Card Composition

The agency dashboard should not depend on a new aggregate endpoint in this phase. Summary cards are composed from existing paginated totals:

- listings total → `GET /agency/listings`
- active leads total → `GET /agency/leads?reviewed=false`
- reviewed leads total → `GET /agency/leads?status=reviewed`
- scheduled viewings total → `GET /agency/viewings`

## Non-Contracts

- No AI widgets, chat, voice, or match score contracts exist in this phase.
- No policy upload or spam-lead processing contract exists in this phase.
