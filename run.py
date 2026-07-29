import sys
sys.path.insert(0, "backend")

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,  # 改成 8001
        reload=True,
        log_level="info"
    )