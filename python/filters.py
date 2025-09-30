import cv2 as cv, numpy as np, copy
from collections import deque

class Filters:
    """A simple stack-based undo/redo system for image filters."""
    def __init__(self, maxleen=20):
        self.filters = deque(maxlen=maxleen)
        self.index = -1

    def push(self, filter_dicts: dict):
        """Apply new filters and push to stack."""
        while len(self.filters) - 1 > self.index:
            self.filters.pop()

        self.filters.append(dict(filter_dicts))
        self.index = len(self.filters) - 1

    def undo(self, image):
        if self.index > 0:
            self.index -= 1

            return apply_filters(image, self.filters[self.index])
        return None

    def redo(self, image):
        if self.index < len(self.filters) - 1:
            self.index += 1

            return apply_filters(image, self.filters[self.index])
        return None


def apply_filters(image, filters):
    """Apply a series of filters to an image."""

    # Handle sharpen separately
    sharpen_cfg = filters.get('sharpen', {})
    amount = sharpen_cfg.get('amount', 1.0)
    threshold = sharpen_cfg.get('threshold', 10)

    if amount != 0 or threshold != 0:
        image = unsharp_mask(image, amount=float(amount), threshold=float(threshold))

    # Other filters
    for name, default in {
        "grayscale": 255.0,
        "sepia": 255.0,
        "blur": 255.0,
        "hue": 255.0,
        "saturation": 255.0,
        "contrast": 255.0,
        "brightness": 128.0,
    }.items():
        strength = float(filters.get(name, default))
        if strength != 0:  # <-- skip if zero
            func = globals()[name] # Call all functions
            image = func(image, strength=strength)

    return image


# From OpenCV documentation https://docs.opencv.org/4.x/d1/d10/classcv_1_1MatExpr.html#details
def unsharp_mask(image, kernel_size=(5, 5), sigma=1.0, amount=1.0, threshold=10):
    """Return a sharpened version of the image, using an unsharp mask."""
    blurred = cv.GaussianBlur(image, kernel_size, sigma)
    sharpened = (amount + 1) * image - amount * blurred
    sharpened = np.clip(sharpened, 0, 255).round().astype(np.uint8)
    if threshold > 0:
        low_contrast_mask = np.absolute(image - blurred) < threshold
        np.copyto(sharpened, image, where=low_contrast_mask)
    return sharpened

def grayscale(image, strength=255):
    """Convert image to grayscale."""

    alpha = 1 - (strength / 255.0)
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    gray2bgr = cv.cvtColor(gray, cv.COLOR_GRAY2BGR)
    image = cv.addWeighted(image, alpha, gray2bgr, 1 - alpha, 0)
    return image


# From GeeksforGeeks https://www.geeksforgeeks.org/computer-vision/creating-instagram-filters-with-opencv-and-python/
def sepia(image, strength=255):
    """Apply sepia filter to image."""
    alpha = 1 - (strength / 255.0)
    sepia = np.array([[0.272, 0.534, 0.131],
                  [0.349, 0.686, 0.168],
                  [0.393, 0.769, 0.189]])
    
    sepia_image = cv.transform(image, sepia)
    image = cv.addWeighted(src1=image, alpha=alpha, src2=sepia_image, beta=1 - alpha, gamma=0)
    return image

def blur(image, strength=255):
    """Apply Averaging blur to image."""

    # Ensure minimum of 1 and make it odd
    k = max(1, int(strength))
    if k % 2 == 0:
        k += 1
    ksize = (k, k)
    image = cv.blur(src=image, ksize=ksize)
    return image

def hue(image, strength=255):
    hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    (h, s, v) = cv.split(hsv)

    # Map slider (0–255) → shift (0–179)
    shift = int((strength / 255.0) * 179)

    # Add shift and wrap around (OpenCV hue range is [0,179])
    h = (h.astype(int) + shift) % 180
    h = h.astype(np.uint8)

    merge = cv.merge([h,s,v])
    image = cv.cvtColor(merge, cv.COLOR_HSV2BGR)
    
    return image

def saturation(image, strength=255):
    hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    (h, s, v) = cv.split(hsv)

    # Map slider (0–255) → shift (0–179)
    shift = strength / 128.0

    s = np.clip(s.astype(float) * shift, 0, 255).astype(np.uint8)

    merge = cv.merge([h,s,v])
    image = cv.cvtColor(merge, cv.COLOR_HSV2BGR)

    return image

def contrast(image, strength=255):
    lab = cv.cvtColor(image, cv.COLOR_BGR2Lab)
    (l, a, b) = cv.split(lab)

    scale = strength / 128.0
    
    a = np.clip((a.astype(float) - 128) * scale + 128, 0, 255).astype(np.uint8)
    b = np.clip((b.astype(float) - 128) * scale + 128, 0, 255).astype(np.uint8)

    merge = cv.merge([l,a,b])
    image = cv.cvtColor(merge, cv.COLOR_Lab2BGR)

    return image

def brightness(image, strength=128):
    beta = int(strength - 128)
    image = cv.convertScaleAbs(src=image, alpha=1.0, beta=beta)
    return image

filter = Filters()