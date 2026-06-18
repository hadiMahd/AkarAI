# Quickstart: Listing Page User Agent

## Prerequisites

- Backend, user app, PostgreSQL, Redis, and Vault are running in the local stack.
- Azure OpenAI credentials and LangSmith tracing settings are configured for backend-side assistant runs.
- At least one active public listing exists with:
  - complete listing facts
  - at least one active viewing slot for booking validation
- One signed-in user exists with a complete lead profile.
- One signed-in user exists with an incomplete lead profile for negative-path validation.

## Validation Scenarios

### 1. Listing Fact Q&A

1. Sign in to the user app.
2. Open one active listing detail page.
3. Ask factual questions about that listing in the assistant widget.

Expected:
- Answers stay scoped to the current listing.
- The widget does not answer as a general marketplace assistant.
- No mutation controls appear for pure factual Q&A.

### 2. Confirmable Inquiry Preparation

1. Stay on the same listing detail page with a lead-complete profile.
2. Ask the assistant to contact the agency about the listing.
3. Review the prepared inquiry confirmation card.
4. Click confirm.

Expected:
- The assistant prepares a draft but does not submit it automatically.
- Confirm calls the existing inquiry mutation.
- Cancel clears the pending action without clearing the transcript.

### 3. Incomplete Profile Inquiry Block

1. Sign in as a user whose profile is missing `name` or both contact methods.
2. Ask the assistant to prepare an inquiry.

Expected:
- The flow blocks cleanly before inquiry confirmation.
- The user is routed to `/profile`.
- No lead is created.

### 4. Natural-Language Viewing Match

1. Sign in as a valid user on a listing with active slots.
2. Ask for a viewing with a request such as "tomorrow after 5".
3. Review the matched-slot confirmation card.
4. Click confirm.

Expected:
- The backend returns a real active slot proposal or a clean no-match message.
- Confirm calls the existing booking mutation only once.
- If the slot becomes unavailable, the user sees the existing booking conflict path.

### 5. Unauthenticated Mutation Block

1. Open a listing page without being signed in.
2. Ask the assistant to help book a viewing or send an inquiry.

Expected:
- Factual listing Q&A may still work if allowed by the final implementation.
- Confirmable mutation flow routes to sign-in before any write API is called.

## Focused Test Commands

```bash
docker compose exec backend pytest backend/tests/unit/test_listing_user_assistant.py backend/tests/integration/test_listing_user_assistant_api.py
docker compose exec user-app npm run test -- listing-user-assistant
```

## Trace Check

- Verify one LangSmith trace exists per assistant run.
- Verify trace metadata identifies the listing and tool path without exposing raw secrets or unnecessary PII.
