from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = ROOT / "mikrotik" / "Dockerfile"


def test_mikrotik_image_builds_and_copies_production_frontend() -> None:
    text = DOCKERFILE.read_text(encoding="utf-8")

    assert "FROM node:20-alpine AS frontend-build" in text
    assert "RUN npm run frontend:build && node scripts/verify_frontend_build.mjs" in text
    assert (
        "COPY --from=frontend-build /src/unified-ui/static/frontend-build/ "
        "/app/unified-ui/static/frontend-build/"
    ) in text
    assert (
        "COPY --from=frontend-build /src/unified-ui/static/vendor/ "
        "/app/unified-ui/static/vendor/"
    ) in text
