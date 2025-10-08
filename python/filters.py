import cv2 as cv, numpy as np
from FilterStack import Filters

def apply_filters(image):
    """Apply a series of filters to an image."""

    if Filters.modes == 'cached':
        if not Filters.temp_filters:
            raise ValueError (f"Temp filters: {Filters.temp_filters}, Mode: {Filters.modes}")
        current = Filters.temp_filters[-1]

    elif Filters.modes == 'preview':
        if not Filters.filters or Filters.index < 0 or Filters.index >= len(Filters.filters):
            raise ValueError (f"Mode: {Filters.modes}")
        current = Filters.filters[Filters.index]

    cropped = current.get("crop", {})
    
    for (section, values) in current.items():
        for (name, val) in values.items():
            func = globals().get(name)
            if not callable(func):
                continue

            if isinstance(val, bool) and val:
                image = func(image=image)
            elif isinstance(val, (int, float)) and val != 0:
                image = func(image=image, strength=val)
            elif section == "crop":
                continue

    x = int(cropped.get("x", 0))
    y = int(cropped.get("y", 0))
    w = int(cropped.get("width", 0))
    h = int(cropped.get("height", 0))
    if x>0 and y>0 and w > 0 and h > 0:
        image = crop(image=image, x=x, y=y, w=w, h=h)
                
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

def cool(image):
    # Convert image to float32 for calculations
    image_float = image.astype(np.float32) / 255.0

    # Split channels (assuming BGR format for OpenCV)
    (b, g, r) = cv.split(image_float)

    # Increase blue channel, decrease red channel
    # You can adjust the scaling factors (e.g., 1.2 for blue, 0.8 for red)
    # to control the intensity of the cool effect.
    b_new = np.clip(b * 1.5, 0, 1)  # Increase blue
    r_new = np.clip(r * 0.5, 0, 1)  # Decrease red

    # Merge channels back
    cool = cv.merge([b_new, g, r_new])

    # Convert back to uint8 and scale to 0-255
    cooled_image = (cool * 255).astype(np.uint8)
    return cooled_image

def warm(image):
    # Convert image to float32 for calculations
    image_float = image.astype(np.float32) / 255.0

    # Split channels (assuming BGR format for OpenCV)
    (b, g, r) = cv.split(image_float)

    # Increase blue channel, decrease red channel
    # You can adjust the scaling factors (e.g., 1.2 for blue, 0.8 for red)
    # to control the intensity of the cool effect.
    b_new = np.clip(b * 0.5, 0, 1)  # Increase blue
    r_new = np.clip(r * 1.5, 0, 1)  # Decrease red

    # Merge channels back
    warm = cv.merge([b_new, g, r_new])

    # Convert back to uint8 and scale to 0-255
    warmed_image = (warm * 255).astype(np.uint8)
    return warmed_image

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

# From AskPython https://www.askpython.com/python/examples/adding-noise-images-opencv 
def grain(image, strength=float(0)):
    noise = np.random.randint(-strength, strength + 1, image.shape)
    noisy_image = np.clip(image + noise, 0, 255).astype(np.uint8)
    return noisy_image

# From Geeks2Geeks https://www.geeksforgeeks.org/python/create-a-vignette-filter-using-python-opencv/
def vignette(image, strength=float(0)):
    # Extracting the height and width of an image 
    height, width = image.shape[:2]

    # Normalise strength to 0.0–1.0 (soft fade)
    intensity = np.clip(strength / 100.0, 0.0, 1.0)
    
    # Sigma controls how quickly the edges darken; smaller = stronger vignette
    sigma_x = width * (0.5 - 0.4 * intensity)
    sigma_y = height * (0.5 - 0.4 * intensity)

    # generating vignette mask using Gaussian 
    # resultant_kernels
    X_resultant_kernel = cv.getGaussianKernel(width, sigma_x)
    Y_resultant_kernel = cv.getGaussianKernel(height, sigma_y)
    
    #generating resultant_kernel matrix 
    resultant_kernel = Y_resultant_kernel * X_resultant_kernel.T

    # Normalise mask to [0, 1]
    mask = resultant_kernel / resultant_kernel.max()

    # Invert so edges darken instead of brighten
    mask = 1 - intensity * (1 - mask)
    
    image = np.copy(image)
    
    # applying the mask to each channel in the input image
    for i in range(3):
        image[:,:,i] = image[:,:,i] * mask

    image = np.clip(image, 0, 255).astype(np.uint8)
    return image

def glow(image, strength=float(0)):
    """Add a soft glow effect based on strength (0–100)."""
    if strength <= 0:
        return image

    # Convert slider strength (0–100) to usable 0–1 scale
    intensity = np.clip(strength / 100.0, 0.0, 1.0)

    # Determine blur radius based on image size and intensity
    height, width = image.shape[:2]
    blur_radius = int(max(3, (width + height) / 400 * (5 + 20 * intensity)))

    # Kernel size must be odd
    if blur_radius % 2 == 0:
        blur_radius += 1

    # Apply Gaussian blur
    img_blurred = cv.GaussianBlur(image, (blur_radius, blur_radius), 0)

    # Blend original and blurred images (soft glow)
    glow_img = cv.addWeighted(image, 1.0, img_blurred, 0.5 * intensity, 0)

    image = np.clip(glow_img, 0, 255).astype(np.uint8)

    return image

def crop(image, x=0, y=0, w=0, h=0):
    """Slicing an image based on the given starting and ending coordinates."""
    height, width = image.shape[:2]

    cropped = image[y:y + h, x:x + w]

    if cropped.size == 0:
        raise ValueError(f"[CROP] Empty crop at ({x}, {y}) on image of size {width}x{height}")

    return cropped