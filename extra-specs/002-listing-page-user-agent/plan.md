# Implementation Plan: Listing Page User Agent

**Branch**: `[extra/002-listing-page-user-agent]`

## Summary

Add a user-facing AI assistant on the listing detail page that helps the user send an inquiry or schedule a viewing without inventing new business flows. The agent must orchestrate existing APIs, stay transparent, and require explicit confirmation before mutations.

## Scope

- add a listing-page AI assistant UI in the user app
- support inquiry help based on the current listing context
- support viewing-booking help based on available slots
- reuse existing lead and viewing routes and permission rules
- capture enough audit/debug state to understand agent-triggered actions
- keep profile identity details owned by the profile page, not repeated in inquiry and viewing activity screens unless there is a clear workflow reason

## Non-Goals

- no buyer-to-agency real-time chat
- no autonomous mutation without user confirmation
- no duplicate lead or viewing workflow outside the existing source-of-truth APIs

## Branch Outcome

This branch should produce a safe orchestration layer on the listing page, not a separate domain system.
