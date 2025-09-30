import numpy as np, base64, os, cv2

class FileHandling:
    """Handles image import/export and conversion to/from data URLs."""
    def __init__(self):
        self.images = {}
        self.previews = {}


    def image_to_dataurl(self, image=None, fmt='png'):

        # encode image to memory then to base64 data URL
        ext = str(fmt).lower().strip()

        # Ensure dtype = uint8
        if image.dtype != 'uint8':
            image = image.astype('uint8')

        # Strip alpha for JPEG
        if ext in ["jpg", "jpeg"] and image.ndim == 3 and image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

        success, buffer = cv2.imencode(f'.{ext}', image)
        if not success:
            raise RuntimeError('Failed to encode image')
        b64 = base64.b64encode(buffer).decode('ascii')
        return f'data:image/{fmt};base64,{b64}'

    # Import image
    def save_dataurl_to_memory(self, data_url: str, filename: str):
        """Decode a data URL and save it to disk. Returns the absolute path."""
        
        if ',' not in data_url:
            raise ValueError('Invalid data URL')
        __, b64 = data_url.split(',', 1)
        # Decode base64 into raw bytes
        raw = base64.b64decode(b64)

        np_arr = np.frombuffer(raw, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(f"Failed to decode image: {filename}")
        else:
            self.images[filename] = img


    # Export image
    def load_image_as_dataurl(self, input_path: str, fmt: str = 'jpg'):
        """Read image from disk and return a base64 data URL (uses image_to_dataurl)."""
        if not os.path.isfile(input_path):
            raise FileNotFoundError(input_path)
        image = cv2.imread(input_path)
        if image is None:
            raise RuntimeError(f'Failed to read image: {input_path}')
        return self.image_to_dataurl(image=image, fmt=fmt)