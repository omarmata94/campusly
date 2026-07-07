from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from typing import Optional

import streamlit.components.v1 as components
from PIL import Image

_COMPONENT_DIR = Path(__file__).parent / "camera_component"
_rear_camera = components.declare_component(
    "rear_camera_qr",
    path=str(_COMPONENT_DIR),
)


def rear_camera_input(key: str = "rear_cam") -> Optional[Image.Image]:
    """Custom camera component that defaults to the rear camera.
    Returns a PIL Image when the user captures a photo, otherwise None.
    """
    result = _rear_camera(key=key, default=None)
    if not result:
        return None
    try:
        _, data = result.split(",", 1)
        return Image.open(BytesIO(base64.b64decode(data)))
    except Exception:
        return None
