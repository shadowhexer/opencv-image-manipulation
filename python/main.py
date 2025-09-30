import sys,cv2
from NeutralinoExtension import *
from filters import *
from FileHandling import FileHandling

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

        try:
            if func == 'cached':
                fh.previews[filenames] = apply_filters(
                    image=fh.images[filenames], 
                    filters=filters
                )
                resized_image = cv2.resize(fh.previews[filenames], None, fx=0.3, fy=0.3, interpolation=cv2.INTER_AREA)
                image = fh.image_to_dataurl(image=resized_image, fmt='jpeg')
                ext.sendMessage('imageAdjusted', {
                    'status' : True,   
                    'filename' : filenames, 
                    'dataUrl' : image,
                    'filters' : filters
                })

            elif func == 'preview':

                filter.push(filters)
                fh.previews[filenames] = apply_filters(image=fh.images[filenames], filters=filter.filters[-1])
                resized_image = cv2.resize(fh.previews[filenames], None, fx=0.6, fy=0.6, interpolation=cv2.INTER_AREA)
                image = fh.image_to_dataurl(image=resized_image, fmt='png')
                
                ext.sendMessage('imageAdjusted', {
                    'status' : True,   
                    'filename' : filenames, 
                    'dataUrl' : image,
                    'filters' : filters
                })
            
            elif func == 'final':
                export_images = []
                
                for (filename, image) in fh.previews.items():
                     export_images.append({
                        'filename': filename,
                        'url': fh.image_to_dataurl(image=image, fmt='png')
                    })
                
                ext.sendMessage('imageExport', {
                    'status' : True,   
                    'data' : export_images
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