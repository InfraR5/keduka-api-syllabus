import requests
from .config import MOODLE_URL, MOODLE_TOKEN

def call_moodle(function, params):
    payload = {
        "wstoken": MOODLE_TOKEN,
        "wsfunction": function,
        "moodlewsrestformat": "json",
    }
    # User's snippet used **params but explicitly. Let's match their signature.
    # The user snippet: 
    # def call_moodle(function, params):
    #    payload = { ... **params }
    if params:
        payload.update(params)

    r = requests.post(MOODLE_URL, data=payload, timeout=20)
    r.raise_for_status()
    # Moodle returns 200 even for errors often, but let's stick to their basic specific code.
    return r.json()
