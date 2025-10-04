import cv2 as cv, numpy as np, copy
from collections import deque

class Filters:
    """A simple stack-based undo/redo system for image filters."""
    def __init__(self, maxlen=20):
        self.filters = deque(maxlen=maxlen)
        self.temp_filters = deque(maxlen=maxlen)
        self.index = -1

    def push(self, filter_data: list | dict, mode: str):
        """Apply new filters and push to stack."""

        if len(self.temp_filters) == 0:
            return

        if mode == "temp":
            self.temp_filters.append(filter_data)

        elif mode == "preview":
            while len(self.filters) - 1 > self.index:
                self.filters.pop()

            self.filters.append(self.temp_filters[-1])
            self.temp_filters.clear()

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


def apply_filters(image, data: dict):
    """Apply a series of filters to an image."""

    for (section, values) in data.items():
        for (name, val) in values.items():
            func = globals().get(name)
            if not callable(func):
                continue

            if isinstance(val, bool) and val:
                image = func(image=image)
            elif isinstance(val, (int, float)) and val != 0:
                image = func(image=image, strength=val)

    return image


def grayscale(image):
    """Convert image to grayscale."""

    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    image = cv.cvtColor(gray, cv.COLOR_GRAY2BGR)
    return image

# From Filipe Chagas https://gist.github.com/FilipeChagasDev/bb63f46278ecb4ffe5429a84926ff812
def sepia(image):
    """Apply sepia filter to image."""
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    normalized_gray = np.array(gray, np.float32)/255
    #solid color
    sepia = np.ones(image.shape)
    sepia[:,:,0] *= 153 #B
    sepia[:,:,1] *= 204 #G
    sepia[:,:,2] *= 255 #R
    #hadamard
    sepia[:,:,0] *= normalized_gray #B
    sepia[:,:,1] *= normalized_gray #G
    sepia[:,:,2] *= normalized_gray #R
    image = np.array(sepia, np.uint8)
    return image

# Adjustments

def brightness(image, strength=float(0)):
    """Increase or decrease the image's brightness."""
    image = cv.cvtColor(image, cv.COLOR_BGR2HSV).astype("float32")
    (h, s, v) = cv.split(image)
    value = np.clip(v + strength, 0, 255)

    hsv = cv.merge([h, s, value])
    hsv = np.clip(hsv, 0, 255).astype("uint8")
    image = cv.cvtColor(hsv, cv.COLOR_HSV2BGR)
    return image

def contrast(image, strength=float(0)):
    """Apply contrast to the image."""
    lab = cv.cvtColor(image, cv.COLOR_BGR2Lab)
    (l, a, b) = cv.split(lab)

    scale = 1 + (strength / 100.0)
    
    a = np.clip((a.astype(float) - 128) * scale + 128, 0, 255).astype(np.uint8)
    b = np.clip((b.astype(float) - 128) * scale + 128, 0, 255).astype(np.uint8)

    merge = cv.merge([l,a,b])
    image = cv.cvtColor(merge, cv.COLOR_Lab2BGR)

    return image

def saturation(image, strength=float(0)):
    """Apply saturation to the image."""
    hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    (h, s, v) = cv.split(hsv)

    shift = 1 + (strength / 100.0)

    s = np.clip(s.astype(float) * shift, 0, 255).astype(np.uint8)

    merge = cv.merge([h,s,v])
    image = cv.cvtColor(merge, cv.COLOR_HSV2BGR)

    return image

def hue(image, strength=float(0)):
    """Apply hue to the image."""
    hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    (h, s, v) = cv.split(hsv)

    # Add shift and wrap around (OpenCV hue range is [0,179])
    h = (h.astype(int) + strength) % 180
    h = h.astype(np.uint8)

    merge = cv.merge([h,s,v])
    image = cv.cvtColor(merge, cv.COLOR_HSV2BGR)
    
    return image

def blur(image, strength=float(0)):
    """Apply Averaging blur to image."""

    # Ensure minimum of 1 and make it odd
    k = max(1, int(strength))
    if k % 2 == 0:
        k += 1
    ksize = (k, k)
    image = cv.blur(src=image, ksize=ksize)
    return image

# From OpenCV documentation https://docs.opencv.org/4.x/d1/d10/classcv_1_1MatExpr.html#details
def sharpen(image, kernel_size=(5, 5), sigma=1.0, strength=float(0), threshold=10):
    """Return a sharpened version of the image, using an unsharp mask."""
    blurred = cv.GaussianBlur(image, kernel_size, sigma)
    sharpened = (strength + 1) * image - strength * blurred
    sharpened = np.clip(sharpened, 0, 255).round().astype(np.uint8)
    if threshold > 0:
        low_contrast_mask = np.absolute(image - blurred) < threshold
        np.copyto(sharpened, image, where=low_contrast_mask)
    return sharpened

def grain(image, strength=float(0)):
    return image

def vignette(image, strength=float(0)):
    return image

def glow(image, strength=float(0)):
    return image

filter = Filters()