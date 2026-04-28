# alexa_skill.py
# pip install flask requests ask-sdk-core ask-sdk-webservice-support

import os
import json
import oscrypto
oscrypto.use_openssl(
    '/usr/lib/aarch64-linux-gnu/libcrypto.so.3',
    '/usr/lib/aarch64-linux-gnu/libssl.so.3'
)
import requests
from flask import Flask, request, Response
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.utils import is_intent_name, is_request_type
from ask_sdk_webservice_support.webservice_handler import WebserviceSkillHandler

# ── Config ────────────────────────────────────────────────────────────────────
PICO_BASE = os.environ.get("PICO_BASE_URL", "http://192.168.1.1")
SKILL_ID = os.environ.get("SKILL_ID", "unknown")
# ──────────────────────────────────────────────────────────────────────────────

app = Flask(__name__)
sb = SkillBuilder()
sb.skill_id = SKILL_ID

def pico(device: str, action: str) -> bool:
    """Call the Pico REST API. Returns True on success."""
    try:
        r = requests.put(f"{PICO_BASE}/{device}/{action}", timeout=5)
        return r.ok
    except requests.RequestException:
        return False


# ── Handlers ──────────────────────────────────────────────────────────────────

class LaunchHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        return (handler_input.response_builder
                .speak("Porch controller ready. You can turn the camera or light on or off.")
                .ask("What would you like to do?")
                .response)


class ControlDeviceHandler(AbstractRequestHandler):
    """Handles: 'turn the camera on', 'switch the light off', etc."""

    def can_handle(self, handler_input):
        return is_intent_name("ControlDeviceIntent")(handler_input)

    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        device = slots.get("device") and slots["device"].value
        action = slots.get("action") and slots["action"].value

        # Normalise synonyms Alexa might return
        if device:
            device = device.lower()
            if "camera" in device or "cam" in device:
                device = "camera"
            elif "light" in device or "lamp" in device:
                device = "light"

        if action:
            action = action.lower()
            if action in ("on", "off"):
                pass  # already good
            elif action in ("enable", "start", "activate"):
                action = "on"
            elif action in ("disable", "stop", "deactivate"):
                action = "off"

        if device not in ("camera", "light") or action not in ("on", "off"):
            speech = "Sorry, I didn't catch that. You can say things like: turn the light on."
        elif pico(device, action):
            speech = f"Okay, turning the {device} {action}."
        else:
            speech = f"Sorry, I couldn't reach the Pico to turn the {device} {action}."

        return handler_input.response_builder.speak(speech).response


class HelpHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        return (handler_input.response_builder
                .speak("Say: turn the camera on, turn the light off, and so on.")
                .ask("What would you like to do?")
                .response)


class CancelStopHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        return handler_input.response_builder.speak("Goodbye!").response


class SessionEndedHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.response


# Register all handlers
for handler in [LaunchHandler, ControlDeviceHandler, HelpHandler,
                CancelStopHandler, SessionEndedHandler]:
    sb.add_request_handler(handler())

#skill_handler = WebserviceSkillHandler(skill=sb.create())
skill_handler = WebserviceSkillHandler(
    skill=sb.create()
)

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
        print(f"=== ERROR: {type(e).__name__}: {e} ===")
        traceback.print_exc()
        return Response(str(e), status=500)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
