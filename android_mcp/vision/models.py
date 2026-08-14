"""Data models and protocol for vision-based UI element recognition."""

from dataclasses import dataclass, field
from typing import Optional, Protocol


@dataclass
class BoundingBox:
    """Bounding box of a UI element in pixel coordinates."""

    x: int
    y: int
    width: int
    height: int


@dataclass
class Element:
    """A recognized UI element with location and confidence."""

    description: str
    center_x: int
    center_y: int
    confidence: float
    bounds: Optional[BoundingBox] = None


@dataclass
class VisionResult:
    """Unified return type for all vision client implementations."""

    found: bool
    elements: list[Element] = field(default_factory=list)
    raw_response: Optional[str] = None
    error: Optional[str] = None


class VisionClient(Protocol):
    """Protocol for vision model clients."""

    async def analyze_screenshot(
        self,
        base64_image: str,
        target_description: str,
        screen_width: int = 0,
        screen_height: int = 0,
    ) -> VisionResult:
        """Send a screenshot to the vision model and locate a UI element."""
        ...
