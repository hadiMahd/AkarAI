# Tasks: Listing Page User Agent

- [ ] Define the listing-page agent contract around existing inquiry and viewing APIs.
- [ ] Add the user-app assistant UI to the listing detail page.
- [ ] Implement inquiry orchestration that prepares and confirms a lead submission before sending.
- [ ] Implement viewing orchestration that helps select a valid slot and confirms booking before sending.
- [ ] Clean up the user activity surfaces so inquiry and viewing history do not redundantly show profile identity details that belong on the profile page.
- [ ] Add backend guardrails or orchestration helpers only where needed; keep business truth in existing services.
- [ ] Add focused tests for successful inquiry flow, successful booking flow, cancellation, auth failure, and slot/unavailability edge cases.
