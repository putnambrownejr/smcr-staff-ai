import os

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.public_library.app:app",
        host=os.environ.get("SMCR_PUBLIC_BIND_HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8010")),
        access_log=False,
    )
