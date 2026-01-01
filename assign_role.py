
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

MOODLE_URL = os.getenv("MOODLE_URL")
if MOODLE_URL and not MOODLE_URL.endswith("server.php"):
    MOODLE_URL = MOODLE_URL.rstrip("/") + "/webservice/rest/server.php"

# MOODLE_TOKEN = os.getenv("MOODLE_TOKEN")
MOODLE_TOKEN = "2c168d702fd9aff0e5b29ede986d949b" # Using the working admin/service token
MOODLE_HOST = os.getenv("MOODLE_HOST") or "moodle.r5projetos.com.br"

def call_moodle(function, params):
    payload = {
        "wstoken": MOODLE_TOKEN,
        "wsfunction": function,
        "moodlewsrestformat": "json",
    }
    if params:
        payload.update(params)
    
    headers = {
        "Host": MOODLE_HOST,
        "User-Agent": "MoodleMobile"
    }
    
    try:
        r = requests.post(MOODLE_URL, data=payload, headers=headers, verify=False, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Error calling {function}: {e}")
        try:
             print(f"Response text: {r.text[:500]}")
        except:
             pass
        return None

def main():
    USER_ID = 3
    COURSE_ID = 2
    ROLE_ID = 3 # Editing Teacher

    print(f"Assigning Role ID {ROLE_ID} to User ID {USER_ID} in Course {COURSE_ID}...")
    
    # 1. Get Context ID for the course
    print("Fetching course details via core_course_get_courses...")
    params_context = {
        "options[ids][0]": COURSE_ID 
    }
    
    courses = call_moodle("core_course_get_courses", params_context)
    
    context_id = None
    if isinstance(courses, list) and len(courses) > 0:
        target_course = courses[0]
        context_id = target_course.get("contextid")
    else:
        print(f"Could not fetch course info or empty list: {courses}")
        return

    if not context_id:
        print("Context ID not found in course object.")
        # Probe for function availability with a likely invalid context ID
        print("Probing 'core_role_assign_roles' availability with dummy Context ID 99999...")
        params_probe = {
            "assignments[0][roleid]": ROLE_ID,
            "assignments[0][userid]": USER_ID,
            "assignments[0][contextid]": 99999
        }
        resp = call_moodle("core_role_assign_roles", params_probe)
        if isinstance(resp, dict) and 'exception' in resp:
            print(f"Probe Result: {resp['message']} (Error Code: {resp.get('errorcode')})")
        else:
             print(f"Probe Result: Success/Unexpected: {resp}")
        return

    print(f"Found Context ID: {context_id}")
    
    params = {
        "assignments[0][roleid]": ROLE_ID,
        "assignments[0][userid]": USER_ID,
        "assignments[0][contextid]": context_id
    }
    
    print("Attempting core_role_assign_roles...")
    response = call_moodle("core_role_assign_roles", params)
    
    if response is None:
        print("Success: Moodle returned null (expected for void functions). Role assigned.")
    elif isinstance(response, dict) and 'exception' in response:
        print(f"Error: {response['message']}")
    else:
        print(f"Response: {response}")

if __name__ == "__main__":
    main()
