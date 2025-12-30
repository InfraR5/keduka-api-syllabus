import requests
import json

TOKEN = "2c168d702fd9aff0e5b29ede986d949b"
URL = "https://moodle.r5projetos.com.br/webservice/rest/server.php"

def check_course():
    params = {
        "wstoken": TOKEN,
        "wsfunction": "core_course_get_contents",
        "moodlewsrestformat": "json",
        "courseid": 1
    }
    try:
        print(f"Checking Course 1...")
        resp = requests.get(URL, params=params, timeout=10)
        data = resp.json()
        
        if isinstance(data, list):
            print(f"Found {len(data)} sections:")
            for sec in data:
                name = sec.get("name", "Unnamed")
                visible = sec.get("visible", "?")
                modules = len(sec.get("modules", []))
                print(f"- [ID {sec.get('id')}] {name} (Visible: {visible}, Modules: {modules})")
        else:
            print("Error/Unexpected format:", json.dumps(data, indent=2))

    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    check_course()
