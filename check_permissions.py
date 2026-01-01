
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

MOODLE_URL = os.getenv("MOODLE_URL")
# MOODLE_TOKEN = os.getenv("MOODLE_TOKEN")
MOODLE_TOKEN = "2c168d702fd9aff0e5b29ede986d949b"
MOODLE_HOST = os.getenv("MOODLE_HOST") or "moodle.r5projetos.com.br"

if MOODLE_URL and not MOODLE_URL.endswith("server.php"):
    MOODLE_URL = MOODLE_URL.rstrip("/") + "/webservice/rest/server.php"

print(f"URL: {MOODLE_URL}")
print(f"HOST: {MOODLE_HOST}")
# print(f"TOKEN: {MOODLE_TOKEN}") # Do not print token

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
        r = requests.post(MOODLE_URL, data=payload, headers=headers, verify=False, timeout=10) # verify=False just in case of self-signed dev certs
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
    # 0. Check Token User
    print("Checking token info...")
    site_info = call_moodle("core_webservice_get_site_info", {})
    if site_info and 'userid' in site_info:
        print(f"Token belongs to User ID: {site_info['userid']}, Username: {site_info.get('username')}, Fullname: {site_info.get('fullname')}")
        # If the token is FOR instrutor1, we found him.
        if site_info.get('username') == 'instrutor1':
             print("Token identifies as instrutor1.")
             user_id = site_info['userid']
             # Proceed to check courses
    else:
        print(f"Could not get site info: {site_info}")

    # 1. Get User ID for 'instrutor1' (only if not already found)
    if 'user_id' not in locals():
        print("Searching for user 'instrutor1'...")
    users = call_moodle("core_user_get_users_by_field", {
        "field": "username",
        "values[0]": "instrutor1"
    })
    
    print(f"Response: {json.dumps(users, indent=2)}")
    
    if isinstance(users, dict) and 'exception' in users:
        print(f"Moodle Exception: {users['message']}")
        return

    if not users:
        print("User 'instrutor1' not found.")
        return

    user = users[0]
    user_id = user['id']
    print(f"User found: {user.get('fullname')} (ID: {user_id})")

    # 2. Get Enrolled Courses
    print(f"Getting courses for user ID {user_id}...")
    courses = call_moodle("core_enrol_get_users_courses", {
        "userid": user_id
    })
    
    if not courses:
        print("User is not enrolled in any courses.")
        return

    print(f"User is enrolled in {len(courses)} courses.")

    # 3. Check roles in each course
    for course in courses:
        cid = course['id']
        shortname = course['shortname']
        print(f"\nChecking Course: {shortname} (ID: {cid})")
        
        print(f"  Requesting enrolled users for course {cid}...")
        enrolled_users = call_moodle("core_enrol_get_enrolled_users", {
            "courseid": cid
        })
        
        if not enrolled_users or (isinstance(enrolled_users, dict) and 'exception' in enrolled_users):
             print(f"  Failed to get enrolled users: {enrolled_users}")
             continue
             
        print(f"  Found {len(enrolled_users)} users in course.")

        # core_enrol_get_enrolled_users returns list of users with roles
        target_role_info = []
        found_in_course = False
        
        roles_found = {} # id -> shortname

        if enrolled_users:
            for u in enrolled_users:
                if u['id'] == user_id:
                    found_in_course = True
                    roles = u.get('roles', [])
                    print(f"  User {u['username']} roles data: {roles}")
                    for r in roles:
                        target_role_info.append(f"{r['shortname']} (ID: {r['roleid']})")
                
                # Aggregate knowledge about roles
                for r in u.get('roles', []):
                    rid = r['roleid']
                    rname = r['shortname']
                    if rid not in roles_found:
                        roles_found[rid] = rname
        
        print("\n--- Roles Detected in Course ---")
        for rid, rname in sorted(roles_found.items()):
            print(f"Role ID {rid}: {rname}")
        print("--------------------------------\n")

        if found_in_course:
            print(f"  Target User Roles: {', '.join(target_role_info)}")
        else:
            print("  User not found in enrolled list (strange, maybe suspended?)")

if __name__ == "__main__":
    main()
