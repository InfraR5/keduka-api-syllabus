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

    # Force Host header to bypass Cloudflare/IP access issues and match VirtualHost
    headers = {
        "Host": "moodle.r5projetos.com.br",
        "User-Agent": "MoodleMobile" # Also match the mobile app UA just in case
    }
    
    # Internal routing via IP requires disabling SSL verification (Certificate matches domain, not IP)
    try:
        r = requests.post(MOODLE_URL, data=payload, headers=headers, timeout=20, verify=False)
        r.raise_for_status()
        data = r.json()
        
        # Log response for debugging (print to stdout which goes to CloudWatch)
        print(f"[MOODLE LOG] Function: {function} | Status: {r.status_code} | Response: {str(data)[:200]}...")

        if isinstance(data, dict) and "exception" in data:
            raise Exception(f"Moodle Error: {data.get('message')} ({data.get('errorcode')})")
            
        return data
    except Exception as e:
        print(f"[MOODLE ERROR] {str(e)}")
        # Re-raise to be handled by FastAPI or crash safely
        raise e

def update_course(course_id: int, summary: str):
    """
    Updates the course summary using core_course_update_courses.
    """
    params = {
        "courses[0][id]": course_id,
        "courses[0][summary]": summary,
        "courses[0][summaryformat]": 1  # HTML
    }
    return call_moodle("core_course_update_courses", params)

def get_course_contents(course_id: int):
    """
    Get course sections and modules using core_course_get_contents.
    """
    params = {
        "courseid": course_id
    }
    return call_moodle("core_course_get_contents", params)

def update_section(section_id: int, name: str, summary: str = "", visible: int = 1):
    """
    Update a course section properties (visibility, etc).
    NOTE: core_course_edit_section DOES NOT SUPPORT RENAMING in Moodle 4.x.
    Use update_section_name for renaming.
    """
    params = {
        "id": section_id,
        "action": "show" if visible else "hide", # Conforming to proper action signature
        # "name": name, # Not supported by edit_section
    }
    # call_moodle("core_course_edit_section", params) # Disabled for now as we focus on renaming
    pass

def update_section_name(section_id: int, new_name: str):
    """
    Renames a section using core_update_inplace_editable.
    Assumes format_topics.
    """
    params = {
        "component": "format_topics",
        "itemtype": "sectionname",
        "itemid": section_id,
        "value": new_name
    }
    return call_moodle("core_update_inplace_editable", params)

def update_course_numsections(course_id: int, num_sections: int):
    """
    Updates the number of sections in a course using core_course_update_courses.
    This works by setting the 'numsections' option for format_topics.
    """
    params = {
        "courses[0][id]": course_id,
        "courses[0][format]": "topics",
        "courses[0][numsections]": num_sections,
        "courses[0][courseformatoptions][0][name]": "numsections",
        "courses[0][courseformatoptions][0][value]": num_sections
    }
    return call_moodle("core_course_update_courses", params)

def create_course_sections(course_ids: list[int]):
    """
    Creates new sections using core_course_create_sections.
    Pass a list of course IDs. One section is created for each ID in the list.
    To create 3 sections in course 2, pass [2, 2, 2].
    """
    params = {}
    for i, cid in enumerate(course_ids):
        params[f"courseids[{i}]"] = cid
    return call_moodle("core_course_create_sections", params)

def delete_course_sections(section_ids: list[int]):
    """
    Deletes sections using core_course_delete_sections.
    """
    params = {}
    for i, sid in enumerate(section_ids):
        params[f"ids[{i}]"] = sid
    return call_moodle("core_course_delete_sections", params)

def create_moodle_section(course_id: int, section_name: str):
    """
    Creates a new section using the custom local_sectionmanager plugin.
    This replaces the need for update_course_numsections or core_update_inplace_editable hacks.
    """
    params = {
        "courseid": course_id,
        "sections[0][name]": section_name
    }
    # Note: Requires MOODLE_TOKEN to be set to the sectionmanager service token
    # (Checking if current token is compatible happens at runtime)
    return call_moodle("local_sectionmanager_create_sections", params)
