import sys
import os
sys.path.insert(0, "backend")

import uvicorn

if __name__ == "__main__":
    # 生产环境默认关闭 reload
    reload = os.getenv("UVICORN_RELOAD", "false").lower() == "true"
    port = int(os.getenv("PORT", 8001))
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=reload,
        log_level="info"
    )