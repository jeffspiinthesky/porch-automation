import asyncio
from machine import Pin
from microdot import Microdot, Response
from Wifi import Wifi

# Set up relay pins
camera = Pin(16, Pin.OUT)  # GP16, pin 21
light = Pin(17, Pin.OUT)   # GP17, pin 22

# Ensure both relays start OFF
camera.value(0)
light.value(0)

app = Microdot()
Response.default_content_type = 'application/json'

HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Pico Controller</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; max-width: 400px; margin: 40px auto; padding: 0 20px; }
        h1 { font-size: 1.4em; }
        .device { background: #f4f4f4; border-radius: 8px; padding: 16px; margin: 12px 0; display: flex; align-items: center; justify-content: space-between; }
        .device span { font-size: 1.1em; font-weight: bold; }
        .btn { padding: 10px 24px; border: none; border-radius: 6px; font-size: 1em; cursor: pointer; }
        .btn-on  { background: #2ecc71; color: white; }
        .btn-off { background: #e74c3c; color: white; }
        .status  { font-size: 0.85em; color: #666; margin-top: 4px; }
    </style>
</head>
<body>
    <h1>Pico Controller</h1>

    <div class="device">
        <div>
            <span>Camera</span>
            <div class="status" id="camera-status">Loading...</div>
        </div>
        <div>
            <button class="btn btn-on"  onclick="control('camera', 'on')">On</button>
            <button class="btn btn-off" onclick="control('camera', 'off')">Off</button>
        </div>
    </div>

    <div class="device">
        <div>
            <span>Light</span>
            <div class="status" id="light-status">Loading...</div>
        </div>
        <div>
            <button class="btn btn-on"  onclick="control('light', 'on')">On</button>
            <button class="btn btn-off" onclick="control('light', 'off')">Off</button>
        </div>
    </div>

    <script>
        async function getState(device) {
            const r = await fetch('/' + device);
            const data = await r.json();
            document.getElementById(device + '-status').textContent = 'State: ' + data.state.toUpperCase();
        }

        async function control(device, action) {
            await fetch('/' + device + '/' + action, {method: 'PUT'});
            getState(device);
        }

        // Poll state every 3 seconds so it stays current
        function refresh() {
            getState('camera');
            getState('light');
        }
        refresh();
        setInterval(refresh, 3000);
    </script>
</body>
</html>"""

# --- Web page ---

@app.get('/')
async def index(request):
    return HTML, 200, {'Content-Type': 'text/html'}

# --- Camera endpoints ---

@app.get('/camera')
async def get_camera(request):
    return {'device': 'camera', 'state': 'on' if camera.value() else 'off'}

@app.put('/camera/on')
async def camera_on(request):
    camera.value(1)
    return {'device': 'camera', 'state': 'on'}

@app.put('/camera/off')
async def camera_off(request):
    camera.value(0)
    return {'device': 'camera', 'state': 'off'}

# --- Light endpoints ---

@app.get('/light')
async def get_light(request):
    return {'device': 'light', 'state': 'on' if light.value() else 'off'}

@app.put('/light/on')
async def light_on(request):
    light.value(1)
    return {'device': 'light', 'state': 'on'}

@app.put('/light/off')
async def light_off(request):
    light.value(0)
    return {'device': 'light', 'state': 'off'}

# --- Start up ---

async def main():
    wifi = Wifi()
    ip = wifi.connect()
    print(f'Server running at http://{ip}')
    await app.run(port=80)

asyncio.run(main())