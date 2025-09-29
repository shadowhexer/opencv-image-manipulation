#!/usr/bin/env python3
import sys
import json
import uuid
from websocket import WebSocketApp
import main
from pathlib import Path

# Image processing is delegated to processor.process_and_dataurl

# Read init JSON from stdin (Neutralino sends it on process start)
init_data = sys.stdin.read()
if not init_data:
    print("ERROR: no init data on stdin", file=sys.stderr)
    sys.exit(1)

cfg = json.loads(init_data)
NL_PORT = cfg.get("nlPort")
NL_TOKEN = cfg.get("nlToken")
NL_CTOKEN = cfg.get("nlConnectToken")
NL_EXTID = cfg.get("nlExtensionId")

if not NL_PORT or not NL_CTOKEN:
    print("ERROR: missing connection info", file=sys.stderr)
    sys.exit(2)

ws_url = f"ws://localhost:{NL_PORT}?extensionId={NL_EXTID}&connectToken={NL_CTOKEN}"

def call_app_broadcast(ws, event_name, data_obj):
    payload = {
        "id": str(uuid.uuid4()),
        "method": "app.broadcast",
        "accessToken": NL_TOKEN,
        "data": {
            "event": event_name,
            "data": data_obj
        }
    }
    ws.send(json.dumps(payload))

def on_open(ws):
    # Optionally announce readiness
    print(f"[{NL_EXTID}] connected to Neutralino server", file=sys.stderr)

def on_message(ws, message):
    # incoming messages from Neutralino -> application dispatch calls, etc.
    try:
        msg = json.loads(message)
    except Exception as e:
        print("WARN: failed to parse message", e, file=sys.stderr)
        return

    # Neutralino dispatch messages usually have shape { event, data }
    event = msg.get("event")
    data = msg.get("data", {})

    if event == "adjust":
        # Image adjustments (hue/brightness) are not implemented in this minimal extension.
        call_app_broadcast(ws, "imageError", {"message": "adjust not implemented in this extension"})
    
    elif event == "importImage":
        # Expect data: { filename: 'name.jpg', dataUrl: 'data:image/..;base64,...' }
        filename = data.get('filename')
        data_url = data.get('dataUrl')
        if not filename or not data_url:
            call_app_broadcast(ws, "imageError", {"message": "importImage requires filename and dataUrl"})
            return
        
        try:
            main.save_dataurl_to_file(data_url, filename)
            call_app_broadcast(ws, 'imageImported', { 'path': filename, 'dataUrl': data_url })
        except Exception as e:
            call_app_broadcast(ws, 'imageImported', { 'status': 0, 'message': str(e) })

    # Export image
    elif event == 'getImage':
        # Expect data: { inputPath: 'relative/or/absolute/path' }
        input_path = data.get('inputPath')
        out_fmt = data.get('format', 'jpg')

        try:
            data_url = main.load_image_as_dataurl(input_path, fmt=out_fmt)
            call_app_broadcast(ws, 'imageExported', { 'dataUrl': data_url, 'path': input_path })
        except Exception as e:
            call_app_broadcast(ws, 'imageExported', { 'status': 0, 'message': str(e) })

    elif event == "ping":
        call_app_broadcast(ws, "pong", {"ok": True})

    else:
        # unhandled events can be ignored or logged
        print(f"DEBUG: unhandled event {event}", file=sys.stderr)

def on_close(ws, close_status_code, close_msg):
    print(f"[{NL_EXTID}] ws closed: {close_status_code} {close_msg}", file=sys.stderr)
    # exit once WS closed
    sys.exit(0)

def on_error(ws, error):
    print(f"[{NL_EXTID}] ws error: {error}", file=sys.stderr)

# Create and run the WS app
ws_app = WebSocketApp(ws_url,
                      on_open=on_open,
                      on_message=on_message,
                      on_close=on_close,
                      on_error=on_error)

# Run forever (blocks)
ws_app.run_forever()