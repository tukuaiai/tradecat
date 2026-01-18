"""API Service 入口"""

import uvicorn

from src.config import get_settings


def main():
    settings = get_settings()
    print(f"启动 API Service: http://{settings.HOST}:{settings.PORT}")
    print(f"文档地址: http://{settings.HOST}:{settings.PORT}/docs")

    uvicorn.run(
        "src.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )


if __name__ == "__main__":
    main()
