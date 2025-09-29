Neutralino Extension Guide — Python image processor

This file contains the step-by-step guide, configuration snippets, and ready-to-paste code for connecting a Python image-processing extension to a Neutralino + Vue frontend. It mirrors the guidance and code provided previously.

---

1) Overview

Flow:
- Neutralino spawns your extension and sends a JSON init object on stdin containing nlPort, nlToken, nlConnectToken and nlExtensionId.
- The extension reads that JSON, connects a WebSocket to Neutralino: ws://localhost:{nlPort}?extensionId={extensionId}&connectToken={connectToken}
- Frontend dispatches events to the extension via Neutralino.extensions.dispatch.
- Extension performs image processing and calls Neutralino native API method `app.broadcast` to send the processed data back to the app.
- Frontend listens for the broadcast with `Neutralino.events.on` to receive and display the image (typically a base64 data URL).

Notes:
- This is ideal for a persistent backend where you adjust values dynamically (hue, brightness, etc.).
- If you only need one-off calls, `Neutralino.os.execCommand` calling your CLI `import.py --base64` is simpler. But for dynamic updates, a long-lived extension is better.

---

2) neutralino.config.json snippet

Make sure `enableExtensions` is true and add the extension entry. For development, a `command*` can run Python directly. For production, point to your PyInstaller binary.

Example:

```json
{
  "enableExtensions": true,
  "nativeAllowList": [
    "app.*",
    "events.*",
    "extensions.*"
  ],
  "extensions": [
    {
      "id": "py.image.processor",
      "commandLinux": "python3 ${NL_PATH}/extensions/python/ext.py",
      "commandDarwin": "python3 ${NL_PATH}/extensions/python/ext.py",
      "commandWindows": "python ${NL_PATH}/extensions/python/ext.py"
    }
  ]
}
```

- `${NL_PATH}` resolves to the app path at runtime. Replace with your bundled binary path after packaging.

---

3) Python extension skeleton (ext.py)

Requirements: websocket-client, OpenCV (cv2) or Pillow. Example below uses `websocket-client` and OpenCV.

Save this as `ext.py` inside your extensions folder (development) or compile it with PyInstaller for packaging.

```python
#!/usr/bin/env python3
import sys
import json
import uuid
import base64
from websocket import WebSocketApp
import cv2
import numpy as np
from pathlib import Path

def image_to_dataurl(image, fmt='jpg'):
    success, buffer = cv2.imencode(f'.{fmt}', image)
    if not success:
        raise RuntimeError('Failed to encode image')
    b64 = base64.b64encode(buffer).decode('ascii')
    mime = 'image/png' if fmt == 'png' else 'image/jpeg'
    return f'data:{mime};base64,{b64}'

# Example processing: adjust hue (degrees) and brightness (scale)
def adjust_image(image_path, hue_shift_deg=0, brightness_scale=1.0):
    img = cv2.imread(str(image_path))
    if img is None:
        raise FileNotFoundError(f'Could not read {image_path}')
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.int16)
    hue_shift = int(hue_shift_deg / 2)  # approximate mapping
    hsv[...,0] = (hsv[...,0] + hue_shift) % 180
    hsv[...,2] = np.clip(hsv[...,2] * brightness_scale, 0, 255)
    hsv = hsv.astype(np.uint8)
    out = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    return out

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
    print(f"[{NL_EXTID}] connected to Neutralino server", file=sys.stderr)

def on_message(ws, message):
    try:
        msg = json.loads(message)
    except Exception:
        print("WARN: failed to parse message", file=sys.stderr)
        return

    event = msg.get("event")
    data = msg.get("data", {})

    if event == "adjust":
        input_path = data.get("inputPath") or "1.jpg"
        hue = float(data.get("hue", 0))
        brightness = float(data.get("brightness", 1.0))
        out_fmt = data.get("format", "jpg")
        try:
            img = adjust_image(Path(input_path), hue, brightness)
            data_url = image_to_dataurl(img, fmt=out_fmt)
            call_app_broadcast(ws, "imageUpdated", {"dataUrl": data_url})
        except Exception as e:
            call_app_broadcast(ws, "imageError", {"message": str(e)})
    elif event == "ping":
        call_app_broadcast(ws, "pong", {"ok": True})
    else:
        print(f"DEBUG: unhandled event {event}", file=sys.stderr)


def on_close(ws, close_status_code, close_msg):
    print(f"[{NL_EXTID}] ws closed: {close_status_code} {close_msg}", file=sys.stderr)
    sys.exit(0)

def on_error(ws, error):
    print(f"[{NL_EXTID}] ws error: {error}", file=sys.stderr)

ws_app = WebSocketApp(ws_url,
                      on_open=on_open,
                      on_message=on_message,
                      on_close=on_close,
                      on_error=on_error)

ws_app.run_forever()
```

Important:
- The extension reads stdin once (the init JSON) and then connects via WebSocket.
- It expects `adjust` events from the app, processes the image, then broadcasts `imageUpdated` with `dataUrl`.
- Print debug to stderr to avoid interfering with protocol.

---

4) Vue frontend examples

Dispatch an `adjust` event to the extension:

```js
await Neutralino.extensions.dispatch('py.image.processor', 'adjust', {
  inputPath: './python/1.jpg',
  hue: 30,
  brightness: 1.15,
  format: 'jpg'
});
```

Listen for result broadcasts:

```js
Neutralino.events.on('imageUpdated', (evt) => {
  // event payload shape may differ by Neutralino version; inspect evt.detail
  const dataUrl = evt.detail?.data?.data?.dataUrl ?? evt.detail?.data?.dataUrl;
  // set <img> src
});

Neutralino.events.on('imageError', (evt) => {
  console.error('Extension error', evt);
});
```

Notes:
- The above uses `app.broadcast` from the extension; the frontend receives broadcast events via Neutralino.events.
- You can implement request/response semantics by sending an id in your dispatch payload and including it in the broadcast.

---

5) Packaging with PyInstaller

- Build the extension: `pyinstaller --onefile ext.py`
- Place the resulting binary under your bundle's extensions folder and update `neutralino.config.json` `commandLinux`/`commandWindows`/`commandDarwin` to point to the binary (e.g., `${NL_PATH}/extensions/binary/linux/processor`).
- OpenCV may need additional PyInstaller hooks (test the binary locally).

---

6) Troubleshooting & security

- Always include `NL_TOKEN` when calling native methods (we use it as accessToken in app.broadcast).
- Keep `nativeAllowList` minimal. Don't expose unnecessary native calls from the frontend.
- If you get token errors, ensure your config sets `enableExtensions: true` and the extension is started by Neutralino (not run standalone without the init JSON).
- For dev, you can run the ext.py standalone by passing a fake JSON to stdin; but the proper behavior requires Neutralino to provide the init object.

---

7) Quick local testing tip

To simulate Neutralino init JSON for development (outside of Neutralino), run:

```bash
python3 ext.py <<'EOF'
{"nlPort":"<port>","nlToken":"<token>","nlConnectToken":"<connect>","nlExtensionId":"py.image.processor"}
EOF
```

This only helps if you've got a Neutralino server running to accept the WebSocket. Otherwise, test the image processing functions locally by importing them into a separate test script.

---

If you'd like I can also:
- Add this file to your README or create a separate `ext.py` in your workspace (I detected an `ext.py` already; I didn't overwrite it).
- Create a small Vue demo page that dispatches changes using sliders and displays results live.
- Help run `pyinstaller` for the extension and adjust `neutralino.config.json` automatically.

Path: neutralino-extension-guide.md

