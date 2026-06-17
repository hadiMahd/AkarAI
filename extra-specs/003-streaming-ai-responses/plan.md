# Implementation Plan: Streaming AI Responses

**Branch**: `[extra/003-streaming-ai-responses]`

## Summary

Add token streaming to chatbot and RAG-style answer surfaces so users stop waiting on a blank or frozen UI. Start with the existing agency RAG chat, then keep the implementation reusable for future chat surfaces such as the listing-page user agent.

## Scope

- add backend streaming support for chat or RAG answer generation
- add frontend incremental rendering for streamed assistant output
- preserve citations, debug metadata, and guardrail outcomes
- support graceful fallback to non-streaming responses when streaming is unavailable
- establish a reusable streaming pattern for later AI surfaces

## Non-Goals

- no semantic cache in this phase
- no new retrieval logic or ranking logic beyond what streaming needs
- no removal of existing non-streaming compatibility

## Branch Outcome

This branch should improve perceived responsiveness across AI chat surfaces without changing source-of-truth business flows.
