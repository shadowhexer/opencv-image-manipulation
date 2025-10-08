import sys, cv2
from NeutralinoExtension import *
from filters import apply_filters, crop
from FilterStack import Filters
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
                # Push the filters in the stack
                Filters.modes = func
                filter.push(filter_data=filters)
                
                fh.previews[filenames] = apply_filters(image=fh.images[filenames])

                image = fh.image_to_dataurl(image=fh.previews[filenames], fmt='jpeg')
                ext.sendMessage('imageAdjusted', {
                    'status' : True,   
                    'filename' : filenames, 
                    'dataUrl' : image,
                    'filters' : Filters.temp_filters[-1]
                })

            elif func == 'preview':
                Filters.modes = func
                filter.push(filter_data=filters)
                fh.previews[filenames] = apply_filters(image=fh.images[filenames])
                image = fh.image_to_dataurl(image=fh.previews[filenames], fmt='png')
                
                ext.sendMessage('imageAdjusted', {
                    'status' : True,   
                    'filename' : filenames, 
                    'dataUrl' : image,
                    'filters' : Filters.filters[Filters.index]
                })

            elif func == 'undo':
                Filters.modes = func
                data = filter.undo()

                fh.previews[filenames] = apply_filters(image=fh.images[filenames])
                image = fh.image_to_dataurl(image=fh.previews[filenames], fmt='png')

                ext.sendMessage('imageAdjusted', {
                    'status' : True,   
                    'filename' : filenames, 
                    'dataUrl' : image,
                    'filters' : data
                })

            elif func == 'redo':
                Filters.modes = func
                data = filter.redo()

                fh.previews[filenames] = apply_filters(image=fh.images[filenames])
                image = fh.image_to_dataurl(image=fh.previews[filenames], fmt='png')

                ext.sendMessage('imageAdjusted', {
                    'status' : True,   
                    'filename' : filenames, 
                    'dataUrl' : image,
                    'filters' : data
                })

            elif func == 'reset':
                Filters.modes = func
                filter.reset()
                image = fh.image_to_dataurl(image=fh.images[filenames], fmt='png')
                ext.sendMessage('imageAdjusted', {
                    'status' : True,   
                    'filename' : filenames, 
                    'dataUrl' : image,
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
            ext.sendMessage('imageAdjusted', {'status' : False, 'message' : f'Error message: {str(e)}. Extra message: { Filters.filters[Filters.index] }'})

    elif ext.isEvent(msg, 'ping'):
        ext.sendMessage("pong", {"ok": True})

    else:
        # unhandled events can be ignored or logged
        print(f"DEBUG: unhandled event {msg.get('event')}", file=sys.stderr)

fh = FileHandling()
filter = Filters()

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    print('running in a PyInstaller bundle')
else:
    print('running in a normal Python process')

ext = NeutralinoExtension(debug=True)
ext.run(main)
