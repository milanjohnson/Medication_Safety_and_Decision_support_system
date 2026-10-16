# SOURCE: NOT IN PAPERS (own tooling). Writes the API's OpenAPI schema so the web app's TypeScript
# types are generated from it (web/scripts/gen-types.mjs) instead of copied by hand.
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from api.app import app  # noqa: E402

out = Path(sys.argv[1])
out.write_text(json.dumps(app.openapi(), indent=1), encoding="utf-8")
print(f"wrote {out}")
