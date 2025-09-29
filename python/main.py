import numpy as np, base64, sys, os, cv2
from NeutralinoExtension import *
from filters import *

# holds the last loaded image as OpenCV BGR array
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

            ext.sendMessage('debugLog', {
                'step': 'AFTER_IMPORT',
                'filename': filename,
                'shape': img.shape,
                'keys_count': len(self.images),
                'keys': list(self.images.keys())
            })


    # Export image
    def load_image_as_dataurl(self, input_path: str, fmt: str = 'jpg'):
        """Read image from disk and return a base64 data URL (uses image_to_dataurl)."""
        if not os.path.isfile(input_path):
            raise FileNotFoundError(input_path)
        image = cv2.imread(input_path)
        if image is None:
            raise RuntimeError(f'Failed to read image: {input_path}')
        return self.image_to_dataurl(image=image, fmt=fmt)


def main(msg):

    if ext.isEvent(msg, 'importImage'):
       
        (__, data) = ext.parseFunctionCall(msg)
        filename = data.get('filename')
        data_url = data.get('dataUrl')

        if not filename or not data_url:
            ext.sendMessage("imageImported", {'status' : False, 'message' : "importImage requires filename and dataUrl"})
            return
        
        try:
            fh.save_dataurl_to_memory(data_url=data_url, filename=filename)
            ext.sendMessage('imageImported', {
                'status' : True, 
                'filename' : filename, 
                'dataUrl' : fh.image_to_dataurl(image=fh.images[filename], fmt='png')
            })
        except Exception as e:
            ext.sendMessage('imageImported', {'status' : False, 'message' : str(e)})
    
    elif ext.isEvent(msg, 'adjustImage'):
        (func, data) = ext.parseFunctionCall(msg)
        filenames = data.get('filename')
        filters = data.get('filters', {})

        ext.sendMessage('debugLog', {
            'step': 'BEFORE_LOOKUP',
            'filename': filenames,
            'keys_count': len(fh.images),
            'first_keys': list(fh.images.keys())[:5]
        })

        try:
            if func == 'final':

                fh.previews[filenames] = apply_filters(image=fh.images[filenames], filters=filters)
                image = fh.image_to_dataurl(image=fh.previews[filenames], fmt='png')
                
                ext.sendMessage('imageAdjusted', {
                    'status' : True,   
                    'filename' : filenames, 
                    'dataUrl' : image,
                    'filters' : filters
                })

            elif func == 'preview':
                fh.previews[filenames] = apply_filters(
                    image=fh.previews[filenames] if filenames in fh.previews else fh.images[filenames], 
                    filters=filters
                )
                image = fh.image_to_dataurl(image=fh.previews[filenames], fmt='jpeg')
                ext.sendMessage('imageAdjusted', {
                    'status' : True,   
                    'filename' : filenames, 
                    'dataUrl' : image,
                    'filters' : filters
                })
        except Exception as e:

            ext.sendMessage('imageAdjusted', {'status' : False, 'message' : str(e)})

    # Export image
    elif ext.isEvent(msg, 'getImage'):
        # Expect data: { inputPath: 'relative/or/absolute/path' }
        input_path = data.get('inputPath')
        out_fmt = data.get('format', 'jpg')

        try:
            data_url = fh.image_to_dataurl(image=fh.images[filename], fmt='jpeg')
            ext.sendMessage('imageExported', {'status' : True, 'dataUrl': data_url})
        except Exception as e:
            ext.sendMessage('imageExported', { 'status': False, 'message': str(e) })

    elif ext.isEvent(msg, 'ping'):
        ext.sendMessage("pong", {"ok": True})

    else:
        # unhandled events can be ignored or logged
        print(f"DEBUG: unhandled event {msg.get('event')}", file=sys.stderr)

fh = FileHandling()
filter = Filters()

ext = NeutralinoExtension(debug=True)
ext.run(main)