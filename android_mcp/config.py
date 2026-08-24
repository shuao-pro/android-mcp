import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Android HTTP tunnel (ADB forward)
    ANDROID_HOST: str = os.getenv("ANDROID_HOST", "127.0.0.1")
    ANDROID_PORT: int = int(os.getenv("ANDROID_PORT", "18080"))
    ANDROID_BASE_URL: str = f"http://{ANDROID_HOST}:{ANDROID_PORT}"
    # Shared auth token for the Android bridge (shown in the app UI)
    ANDROID_TOKEN: str = os.getenv("ANDROID_TOKEN", "")

    # Request timeout (seconds)
    REQUEST_TIMEOUT: float = float(os.getenv("REQUEST_TIMEOUT", "30.0"))

    # Safety guard for high-risk device operations.
    # permissive = allow everything; confirm = require user approval (default);
    # strict = block high/medium-risk operations.
    SAFETY_MODE: str = os.getenv("SAFETY_MODE", "confirm")

    # AI multi-step agent loop (web chat)
    AGENT_MAX_STEPS: int = int(os.getenv("AGENT_MAX_STEPS", "10"))
    AGENT_VISUAL: bool = os.getenv("AGENT_VISUAL", "true").strip().lower() in ("1", "true", "yes", "on")
    AGENT_MAX_RETRIES: int = int(os.getenv("AGENT_MAX_RETRIES", "2"))
    AGENT_MAX_CONSECUTIVE_FAILURES: int = int(os.getenv("AGENT_MAX_CONSECUTIVE_FAILURES", "3"))

    # Web GUI
    WEB_HOST: str = os.getenv("WEB_HOST", "127.0.0.1")
    WEB_PORT: int = int(os.getenv("WEB_PORT", "8080"))

    # MCP SSE server (HTTP transport for web frontends)
    # Defaults to loopback for security; set to 0.0.0.0 to serve LAN clients.
    MCP_HOST: str = os.getenv("MCP_HOST", "127.0.0.1")
    MCP_PORT: int = int(os.getenv("MCP_PORT", "9000"))

    # Screenshot save path
    SCREENSHOT_DIR: str = os.getenv("SCREENSHOT_DIR", "./screenshots")

    # Vision model config (UI element recognition)
    VISION_PROVIDER: str = os.getenv("VISION_PROVIDER", "")
    VISION_API_KEY: str = os.getenv("VISION_API_KEY", "")
    VISION_API_BASE: str = os.getenv("VISION_API_BASE", "")
    VISION_MODEL: str = os.getenv("VISION_MODEL", "")

    def validate(self) -> list[str]:
        """Validate configuration and return a list of warnings (empty = all good)."""
        warnings = []

        for name, label in [
            ("ANDROID_PORT", "ANDROID_PORT"),
            ("WEB_PORT", "WEB_PORT"),
            ("MCP_PORT", "MCP_PORT"),
        ]:
            port = getattr(self, label, 0)
            if not isinstance(port, int) or port < 1 or port > 65535:
                warnings.append(f"{label}={port} is not a valid port (1-65535)")

        if self.REQUEST_TIMEOUT <= 0:
            warnings.append(
                f"REQUEST_TIMEOUT={self.REQUEST_TIMEOUT} must be positive"
            )

        valid_safety_modes = ("permissive", "confirm", "strict")
        if self.SAFETY_MODE.strip().lower() not in valid_safety_modes:
            warnings.append(
                f"SAFETY_MODE={self.SAFETY_MODE!r} is invalid. "
                f"Use: permissive, confirm, or strict"
            )

        if self.AGENT_MAX_STEPS < 1 or self.AGENT_MAX_STEPS > 50:
            warnings.append(
                f"AGENT_MAX_STEPS={self.AGENT_MAX_STEPS} is out of range (1-50)"
            )

        valid_providers = ("anthropic", "openai", "custom")
        if self.VISION_PROVIDER and self.VISION_PROVIDER not in valid_providers:
            warnings.append(
                f"VISION_PROVIDER={self.VISION_PROVIDER!r} is invalid. "
                f"Use: anthropic, openai, or custom"
            )
        if self.VISION_PROVIDER and not self.VISION_API_KEY:
            warnings.append("VISION_PROVIDER is set but VISION_API_KEY is empty")
        if self.VISION_PROVIDER == "custom" and not self.VISION_API_BASE:
            warnings.append("VISION_PROVIDER=custom requires VISION_API_BASE")

        return warnings


config = Config()
