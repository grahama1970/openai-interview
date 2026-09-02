"""One-command local dev server for the interview control plane."""
from __future__ import annotations

import uvicorn


def main() -> None:
    """Run FastAPI with reload on the interview demo port."""
    uvicorn.run("openai_interview.main:app", host="127.0.0.1", port=18081, reload=True)


if __name__ == "__main__":
    main()
