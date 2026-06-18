# Quality Pipeline

This repo now uses one shared quality command layout for local runs, Docker runs,
and GitHub Actions.

## Required merge gates

These are deterministic and should stay provider-independent:

- `make quality-precommit`
- `make quality-backend`
- `make quality-user`
- `make quality-agency`
- `make quality-admin`
- `make quality-workers`
- `make quality-model-service`

`quality.yml` runs those slices in CI.

## Live RAGAS

- `make quality-rag-eval`

It only runs when:

- `USE_RAGAS_EVALS=1`

It self-seeds fixture tenants and uses Azure OpenAI as the judge.

Default behavior:

- `RAG_EVAL_MODE=blocking` runs the blocking 20-example suite
- `RAG_EVAL_MODE=manual` runs the fuller 40-example suite
- `RAG_EVAL_ALLOW_JUDGE_FAILURES=1` is only for non-blocking manual runs

The GitHub workflow is `.github/workflows/rag-evals.yml`. It blocks pull requests with the 20-example suite and also supports manual dispatch for the fuller suite.

## Local commands

```bash
make quality-precommit
make quality-backend
make quality-user
make quality-agency
make quality-admin
make quality-workers
make quality-model-service
make quality-ci
```

## Docker commands

Use these when you want to validate against the same containerized stack the
repo already uses for backend services.

```bash
make docker-quality-backend
make docker-quality-admin
make docker-quality-workers
make docker-quality-model-service
```

## Pre-commit setup

```bash
pip install pre-commit
pre-commit install
```

The hook set covers:

- whitespace / file hygiene
- YAML / JSON / TOML validation
- Python lint + format with `ruff`
- user/agency TypeScript build validation on changed app files
