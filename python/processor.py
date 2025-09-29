"""
Image processing helpers used by the Neutralino extension.
Provides:
- adjust_image(input_path, hue_shift_deg=0, brightness_scale=1.0) -> numpy.ndarray
- image_to_dataurl(image, fmt='jpg') -> str
- process_and_dataurl(input_path, hue, brightness, fmt='jpg') -> str

This file keeps all image logic separate from the extension websocket code.
"""
from pathlib import Path
import base64
import cv2
import numpy as np


def image_to_dataurl(image, fmt='jpg'):
    """Encode an OpenCV image (BGR) to a data URL (jpeg/png)."""
    success, buffer = cv2.imencode(f'.{fmt}', image)
    if not success:
        raise RuntimeError('Failed to encode image')
    b64 = base64.b64encode(buffer).decode('ascii')
    mime = 'image/png' if fmt == 'png' else 'image/jpeg'
    return f'data:{mime};base64,{b64}'


def adjust_image(image_path, hue_shift_deg=0, brightness_scale=1.0):
    """Read image from disk, adjust hue and brightness, return BGR image."""
    p = Path(image_path)
    img = cv2.imread(str(p))
    if img is None:
        raise FileNotFoundError(f'Could not read {image_path}')
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.int16)
    # OpenCV hue is 0..179; map degrees -> half-units approx
    hue_shift = int(hue_shift_deg / 2)
    hsv[..., 0] = (hsv[..., 0] + hue_shift) % 180
    hsv[..., 2] = np.clip(hsv[..., 2] * brightness_scale, 0, 255)
    hsv = hsv.astype(np.uint8)
    out = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    return out


def process_and_dataurl(input_path, hue=0, brightness=1.0, fmt='jpg'):
    img = adjust_image(input_path, hue_shift_deg=hue, brightness_scale=brightness)
    return image_to_dataurl(img, fmt=fmt)
