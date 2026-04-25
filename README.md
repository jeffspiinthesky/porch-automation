# Porch Light and Webcam Automation

# Introduction
This is a fun project to control a standard ceiling light and a webcam from a Raspberry PI Pico W, connected to two relays.

Web services running on the Pico can then be used to turn the light and the webcam on and off. 

Beyond this basic control, it opens the door to be able to do other automations in the future such as:
* Facial recognition
* Motion detection
* Parcel detection
* ...etc

# Setup

* Install Thonny e.g. ```apt install thonny```
* Install MicroPython firmware on the PI Pico W 
* Download [Microdot](https://github.com/miguelgrinberg/microdot/blob/main/src/microdot/microdot.py)
* Create a /lib directory on your Pico and move into it
* Right-click microdot.py and select 'Upload to /lib'
* Click 'Raspberry PI Pico' to return to the root directory 

# Configure WiFi
* Edit the file wifi-creds.json and provide your WiFi details
* Right-click wifi-creds.json and select 'Upload to /'
* Right-click Wify.py and select 'Upload to /'

# Upload main application
* Right-click main.py and select 'Upload to /'

# Using the application
* Either run the application within Thonny and note the IP address allocated to your device or find it from your router
* OPTIONAL: Configure your router to ALWAYS assign that IP address to the Pico
* On your phone or PC, open a browser and navigate to the IP address of the Pico
* Click the 'On' and 'Off' buttons against the light and the camera as desired

# Porch Controller — Alexa Skill Code Walkthrough

## Overview

The porch controller consists of two separate pieces of code running together:

1. **`main.py`** — MicroPython running on a Raspberry Pi Pico W, controlling the physical relays for the camera and light via a small built-in web server
2. **`alexa_skill.py`** — A Python Flask application running on a local machine, acting as the bridge between Amazon's Alexa service and the Pico

The overall request flow is:

```
Echo Device → Amazon Cloud → NGINX Proxy Manager → Flask (alexa_skill.py) → Pico W (main.py)
```

---

## main.py — The Pico W Web Server

### Hardware Setup

```python
from machine import Pin

camera = Pin(16, Pin.OUT)  # GP16, pin 21
light = Pin(17, Pin.OUT)   # GP17, pin 22

camera.value(0)
light.value(0)
```

Two GPIO pins are configured as outputs, each connected to a relay. Pin 16 controls the camera and Pin 17 controls the light. Both are explicitly set to `0` (off) on startup to ensure a known safe state regardless of the relay's previous condition.

### Web Framework

```python
from microdot import Microdot, Response

app = Microdot()
Response.default_content_type = 'application/json'
```

Microdot is a lightweight web framework designed specifically for MicroPython — it is similar in style to Flask but small enough to run on microcontroller hardware. All responses default to JSON format.

### REST API Endpoints

The Pico exposes a simple REST API with three endpoint pairs — one for status and two for control:

|Method|Path|Action|
|---|---|---|
|GET|`/camera`|Returns current camera state|
|PUT|`/camera/on`|Turns camera relay on|
|PUT|`/camera/off`|Turns camera relay off|
|GET|`/light`|Returns current light state|
|PUT|`/light/on`|Turns light relay on|
|PUT|`/light/off`|Turns light relay off|

Example response from any endpoint:

```json
{ "device": "camera", "state": "on" }
```

PUT is used for control actions rather than POST because these are idempotent operations — calling `/camera/on` ten times has the same result as calling it once.

### HTML Control Page

The Pico also serves a built-in HTML control page at `/` which provides a simple browser-based interface for manually toggling the devices. It uses JavaScript `fetch()` calls to hit the same REST endpoints and polls for current state every 3 seconds.

### Startup

```python
async def main():
    wifi = Wifi()
    ip = wifi.connect()
    print(f'Server running at http://{ip}')
    await app.run(port=80)

asyncio.run(main())
```

On boot the Pico connects to WiFi using a separate `Wifi` helper class, then starts the web server on port 80. The entire application is asynchronous, allowing the web server to handle multiple requests without blocking.

---

## alexa_skill.py — The Alexa Skill Server

### SSL Workaround

```python
import oscrypto
oscrypto.use_openssl(
    '/usr/lib/aarch64-linux-gnu/libcrypto.so.3',
    '/usr/lib/aarch64-linux-gnu/libssl.so.3'
)
```

The ASK SDK uses the `oscrypto` library to verify Amazon's request signatures. On ARM-based Linux systems (such as a Raspberry Pi) the library sometimes fails to locate the correct SSL libraries automatically. These two lines explicitly point it to the correct OpenSSL shared libraries for the `aarch64` architecture, preventing a crash on startup.

### Flask and ASK SDK Imports

```python
from flask import Flask, request, Response
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.utils import is_intent_name, is_request_type
from ask_sdk_webservice_support.webservice_handler import WebserviceSkillHandler
```

- **Flask** provides the HTTP server that receives requests from Alexa via NGINX
- **SkillBuilder** assembles the skill from its component handlers
- **AbstractRequestHandler** is the base class all intent handlers inherit from
- **is_intent_name / is_request_type** are utility functions used to match incoming requests to the correct handler
- **WebserviceSkillHandler** wraps the skill and handles Amazon's request signature verification automatically

### Pico Communication

```python
PICO_BASE = "http://<YOUR_PICO_IP>"

def pico(device: str, action: str) -> bool:
    try:
        r = requests.put(f"{PICO_BASE}/{device}/{action}", timeout=5)
        return r.ok
    except requests.RequestException:
        return False
```

This helper function sends a PUT request to the Pico's REST API. It returns `True` on success and `False` on any network error, allowing handlers to give Alexa an appropriate spoken response either way. The 5 second timeout prevents the skill from hanging if the Pico is unreachable.

### Request Handlers

Each handler is a class with two methods:

- **`can_handle()`** — returns `True` if this handler should process the current request
- **`handle()`** — processes the request and returns an Alexa response

#### LaunchHandler

```python
class LaunchHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        return (handler_input.response_builder
                .speak("Porch controller ready. You can turn the camera or light on or off.")
                .ask("What would you like to do?")
                .response)
```

Triggered when the user says _"Alexa, open porch controller"_. The `.ask()` call keeps the session open waiting for a follow-up command.

#### ControlDeviceHandler

```python
class ControlDeviceHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("ControlDeviceIntent")(handler_input)

    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        device = slots.get("device") and slots["device"].value
        action = slots.get("action") and slots["action"].value
        ...
```

This is the main handler, triggered when Alexa recognises a `ControlDeviceIntent`. It extracts the `device` and `action` slot values from the request — these are the words Alexa identified in the user's utterance.

The handler then normalises the values to handle synonyms:

```python
if "camera" in device or "cam" in device:
    device = "camera"
elif "light" in device or "lamp" in device:
    device = "light"
```

This is necessary because Alexa may return a synonym (e.g. "porch light") rather than the canonical slot value ("light"). The normalisation ensures the Pico API always receives a clean, expected value.

If the device and action are valid, it calls `pico()` and constructs an appropriate spoken response. If anything is unrecognised it tells the user what went wrong.

#### Built-in Intent Handlers

```python
class HelpHandler(AbstractRequestHandler):
class CancelStopHandler(AbstractRequestHandler):
class SessionEndedHandler(AbstractRequestHandler):
```

These handle Alexa's built-in intents — `AMAZON.HelpIntent`, `AMAZON.CancelIntent`, `AMAZON.StopIntent`, and `SessionEndedRequest`. These are required by Alexa for any published skill and good practice for development skills. The session ended handler is particularly important — it allows the skill to clean up gracefully when a user stops the skill or the session times out.

### Skill Assembly

```python
sb = SkillBuilder()
sb.skill_id = "amzn1.ask.skill.xxxx..."

for handler in [LaunchHandler, ControlDeviceHandler, HelpHandler,
                CancelStopHandler, SessionEndedHandler]:
    sb.add_request_handler(handler())

skill_handler = WebserviceSkillHandler(skill=sb.create())
```

The `SkillBuilder` assembles all the handlers into a single skill object. The `skill_id` binding ensures that only requests from this specific Alexa skill are accepted — requests from any other skill sharing the endpoint would be rejected. `WebserviceSkillHandler` wraps the skill and adds Amazon request signature verification.

### Flask Route

```python
@app.route("/alexa", methods=["POST"])
def alexa_endpoint():
    try:
        response = skill_handler.verify_request_and_dispatch(
            request.headers, request.data.decode("utf-8")
        )
        if response is None:
            return Response('{"error": "null response"}', status=500, mimetype="application/json")
        return Response(json.dumps(response), mimetype="application/json")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(str(e), status=500)
```

This is the single HTTP endpoint Flask exposes. Every Alexa request arrives here as a POST. The handler:

1. Passes the raw headers and body to the ASK SDK for signature verification and intent dispatching
2. Serialises the response dict to a JSON string with `json.dumps()` — this step is critical, as Alexa requires a properly serialised JSON string, not a Python dict
3. Returns the JSON response with the correct `application/json` content type

---

## Infrastructure

### NGINX Proxy Manager

NGINX sits in front of Flask and handles SSL termination. Alexa requires HTTPS on port 443 — Flask only speaks plain HTTP on port 5000. NGINX receives the encrypted HTTPS request, decrypts it, and forwards it as plain HTTP to Flask. This means Flask never has to deal with SSL certificates directly.

### Alexa Developer Console

The skill is registered in the Alexa Developer Console with:

- **Invocation name**: `porch controller` — the phrase used to open the skill
- **Interaction model**: defines the `ControlDeviceIntent` with `device` and `action` slots, their possible values, and sample utterances
- **Endpoint**: the HTTPS URL of the NGINX proxy pointing to the Flask server
- **Mode**: Development — the skill is private to the registered Amazon account and does not need to go through Amazon's certification process

### Usage

The skill can be invoked in two ways:

**One-shot** (recommended for daily use):

> _"Alexa, tell porch controller to turn the porch light on"_

**Interactive session**:

> _"Alexa, open porch controller"_ _"Turn the camera off"_
