# Research: RAG Storage and Ingestion Foundation

## Unknowns Resolved

### Python and TypeScript Versions
- **Decision**: Python 3.11, TypeScript ^5.5.0.
- **Rationale**: Extracted from existing `backend/Dockerfile` and `apps/agency/package.json` to maintain consistency across the project.
- **Alternatives considered**: None, adhering to existing stack versions.

### Target Platform
- **Decision**: local Docker Compose.
- **Rationale**: Based on user confirmation and existing `docker-compose.yml`.

### Performance Goals
- **Decision**: No specific RAG retrieval latency constraints added beyond the spec's 60 seconds ingestion goal.
- **Rationale**: User replied "no" when asked about specific latency limitations for retrieval at this point. Ingestion must simply complete within 60s per SC-001.

### PDF Parsing Library
- **Decision**: PyMuPDF (`pymupdf`).
- **Rationale**: User deferred choice to the agent. PyMuPDF is extremely fast, production-ready, and robust for extracting clean text from standard PDFs.
- **Alternatives considered**: `pdfplumber` (slower, better for complex tables but overkill for standard policy docs text), `pypdf2` (pure python, occasionally struggles with complex encoding).

### Text Chunking Library
- **Decision**: `fastcdc` (Content-Defined Chunking).
- **Rationale**: The Constitution (Principle VI) explicitly mandates the use of CDC/fastcdc child chunking along with page-level parent chunking and previous-page overlap buffers. FastCDC provides deterministic chunk boundaries resilient to minor text edits, which makes hash comparison and orphan cleanup more stable than recursive character splitters.
- **Alternatives considered**: `langchain-text-splitters` (rejected because it conflicts with the explicit CDC requirement in the constitution), generic python splitters.

