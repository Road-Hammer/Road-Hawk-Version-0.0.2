import uvicorn

from .config import api_host, api_port, api_reload, apply_runtime_config


def main() -> None:
    apply_runtime_config()
    uvicorn.run(
        "road_hawk.api:app",
        host=api_host(),
        port=api_port(),
        reload=api_reload(),
    )


if __name__ == "__main__":
    main()
