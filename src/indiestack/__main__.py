import sys
sys.setrecursionlimit(50000)  # 51 routers × FastAPI lifespan nesting

import uvicorn
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("indiestack.main:app", host="0.0.0.0", port=port, reload=bool(os.environ.get("INDIESTACK_DEBUG")))
