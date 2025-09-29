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

    def undo(self, image, filter_dicts):
        if self.index > 0:
            self.inedx -= 1

            return apply_filters(image, filter_dicts)
        return None

    def redo(self, image, filter_dicts):
        if self.index < len(self.filters) - 1:
            self.index += 1

            return apply_filters(image, filter_dicts)
        return None


def apply_filters(image, filters):
    """Apply a series of filters to an image."""
    
    amount = filters.get('sharpen', {}).get('amount', 1.0)
    threshold = filters.get('sharpen', {}).get('threshold', 10)

    image = unsharp_mask(image, amount=float(amount), threshold=float(threshold))
    image = grayscale(image, alpha=float(filters.get('alpha', 0.5)))
    # Add more filters here as needed

    filter = Filters()
    filter.push(filters)

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

def grayscale(image, alpha=0.5):
    """Convert image to grayscale."""
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    gray2bgr = cv.cvtColor(gray, cv.COLOR_GRAY2BGR)
    image = cv.addWeighted(image, alpha, gray2bgr, 1 - alpha, 0)
    return image