from __future__ import annotations

import argparse
import asyncio

from app.common.cache import cache_invalidate_namespace
from app.common.database import async_session_factory
from app.common.rls import apply_rls_context_to_session
from app.rag.repository import RagRepository
from app.rag.service import RagDocumentService

EVAL_TEST_PATTERNS = [
    "ragas-test-run",
    "ragas-test-run-%",
    "int-test-eval-%",
    "int-fail-eval-%",
]


async def cleanup_failed_documents() -> int:
    async with async_session_factory() as session:
        await apply_rls_context_to_session(session, role="platform_admin", is_platform_admin=True)
        service = RagDocumentService(session)
        return await service.purge_failed_documents()


async def cleanup_test_eval_runs() -> int:
    async with async_session_factory() as session:
        await apply_rls_context_to_session(session, role="platform_admin", is_platform_admin=True)
        repo = RagRepository(session)
        deleted = await repo.delete_evaluation_runs_by_label_patterns(EVAL_TEST_PATTERNS)
        await session.commit()
        return deleted


async def main() -> None:
    parser = argparse.ArgumentParser(description="Clean leaked RAG artifacts from the database.")
    parser.add_argument("--failed-documents", action="store_true", help="Delete failed RAG document rows and blobs.")
    parser.add_argument("--test-evals", action="store_true", help="Delete leaked ad-hoc/test eval runs.")
    args = parser.parse_args()

    if not args.failed_documents and not args.test_evals:
        args.failed_documents = True
        args.test_evals = True

    if args.failed_documents:
        deleted = await cleanup_failed_documents()
        print(f"Deleted failed RAG documents: {deleted}")

    if args.test_evals:
        deleted = await cleanup_test_eval_runs()
        await cache_invalidate_namespace("platform_dashboard:rag_evals")
        print(f"Deleted leaked RAG eval runs: {deleted}")


if __name__ == "__main__":
    asyncio.run(main())
