import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Android HTTP 隧道地址（ADB forward 后的本地端口）
    ANDROID_HOST: str = os.getenv("ANDROID_HOST", "127.0.0.1")
    ANDROID_PORT: int = int(os.getenv("ANDROID_PORT", "18080"))
    ANDROID_BASE_URL: str = f"http://{ANDROID_HOST}:{ANDROID_PORT}"

    # 请求超时（秒）
    REQUEST_TIMEOUT: float = float(os.getenv("REQUEST_TIMEOUT", "30.0"))

    # Web GUI
    WEB_HOST: str = os.getenv("WEB_HOST", "127.0.0.1")
    WEB_PORT: int = int(os.getenv("WEB_PORT", "8080"))

    # MCP SSE server (HTTP transport for web frontends)
    # Use 0.0.0.0 to accept connections from other devices (e.g. phone on same WiFi).
    # Change to 127.0.0.1 if you only need local access.
    MCP_HOST: str = os.getenv("MCP_HOST", "0.0.0.0")
    MCP_PORT: int = int(os.getenv("MCP_PORT", "9000"))

    # 截图保存路径
    SCREENSHOT_DIR: str = os.getenv("SCREENSHOT_DIR", "./screenshots")

    # 视觉模型配置（UI 元素识别）
    VISION_PROVIDER: str = os.getenv("VISION_PROVIDER", "")  # anthropic | openai | custom
    VISION_API_KEY: str = os.getenv("VISION_API_KEY", "")
    VISION_API_BASE: str = os.getenv("VISION_API_BASE", "")  # custom 时必填
    VISION_MODEL: str = os.getenv("VISION_MODEL", "")        # 留空使用 provider 默认模型


config = Config()