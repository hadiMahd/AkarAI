# Implementation Plan: Quality Pipeline

**Branch**: `[extra/001-quality-pipeline]`

## Summary

Raise the project baseline before adding more AI behavior. This phase introduces CI/CD, `pre-commit`, and RAGAS evaluation wiring with a clean split between deterministic checks and optional/live evaluation runs.

## Scope

- add `pre-commit` hooks for formatting, linting, and lightweight hygiene checks
- add CI workflows for backend, frontend, admin, and worker test slices
- add a stable command layout for local verification and CI reuse
- wire RAGAS or equivalent RAG eval execution behind an explicit opt-in path
- keep live/provider-dependent evals out of mandatory merge gates unless later promoted deliberately

## Non-Goals

- no feature work on listing flows
- no semantic cache implementation
- no hidden dependency on live providers for ordinary PR validation

## Branch Outcome

This branch should leave the repo with one reliable quality pipeline that future extra phases can build on safely.
