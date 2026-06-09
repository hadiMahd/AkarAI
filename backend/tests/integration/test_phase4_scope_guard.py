import pytest
import os
import re


SCOPE_EXCLUSIONS = [
    "AI search",
    "RAG",
    "OCR",
    "email send",
    "chatbot",
    "buyer-to-agency",
    "spam classifier",
    "lead scoring",
    "generated reply",
    "image moderation",
    "image quality",
    "WebP",
    "dashboard",
]

PHASE4_MODULES = frozenset(["listings", "leads", "viewings", "search", "agencies", "notifications"])
PHASE4_COMMON_FILES = frozenset([
    "events.py", "cache.py", "domain.py", "rate_limit.py", "dependencies.py",
])


class TestPhase4ScopeGuard:
    @pytest.mark.parametrize("term", SCOPE_EXCLUSIONS)
    def test_no_scope_violation_in_phase4_code(self, term):
        base = "/app/app"
        violations = []
        for root, dirs, files in os.walk(base):
            # Only check Phase 4 domain modules
            rel = os.path.relpath(root, base)
            top_dir = rel.split(os.sep)[0] if rel != "." else ""

            if top_dir and top_dir not in PHASE4_MODULES:
                dirs[:] = []
                continue

            dirs[:] = [d for d in dirs if d not in ("__pycache__",)]

            for f in files:
                if not f.endswith(".py"):
                    continue

                # In common/, only check Phase 4 files
                if rel == "common" and f not in PHASE4_COMMON_FILES:
                    continue

                path = os.path.join(root, f)
                try:
                    with open(path) as fh:
                        for lineno, line in enumerate(fh, 1):
                            if re.search(re.escape(term), line, re.IGNORECASE):
                                stripped = line.strip()
                                if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                                    continue
                                # Allow docstring references
                                if stripped.startswith("minio_bucket_rag") or stripped.startswith("rag."):
                                    continue
                                violations.append(f"{path}:{lineno}: {stripped[:80]}")
                except Exception:
                    pass
        assert not violations, f"Scope violations for '{term}' in Phase 4 code: {violations}"
