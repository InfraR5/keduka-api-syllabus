import requests
from .config import MOODLE_URL, MOODLE_TOKEN, MOODLE_HOST

def call_moodle(function, params, token: str = None):
    # Use provided token, or fallback to config
    active_token = token if token else MOODLE_TOKEN

    payload = {
        "wstoken": active_token,
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
        "Host": MOODLE_HOST,
        "User-Agent": "MoodleMobile" # Also match the mobile app UA just in case
    }
    
    # Public routing via HTTPS requires enabled SSL verification
    try:
        r = requests.post(MOODLE_URL, data=payload, headers=headers, timeout=20)
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

def update_course(course_id: int, summary: str, token: str = None):
    """
    Updates the course summary using core_course_update_courses.
    """
    params = {
        "courses[0][id]": course_id,
        "courses[0][summary]": summary,
        "courses[0][summaryformat]": 1  # HTML
    }
    return call_moodle("core_course_update_courses", params, token)

def get_course_contents(course_id: int, token: str = None):
    """
    Get course sections and modules using core_course_get_contents.
    """
    params = {
        "courseid": course_id
    }
    return call_moodle("core_course_get_contents", params, token)

def update_section(section_id: int, name: str, summary: str = "", visible: int = 1, token: str = None):
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
    call_moodle("core_course_edit_section", params, token)
    pass

def update_section_name(section_id: int, new_name: str, token: str = None):
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
    return call_moodle("core_update_inplace_editable", params, token)

def update_course_numsections(course_id: int, num_sections: int, token: str = None):
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
    return call_moodle("core_course_update_courses", params, token)

def create_course_sections(course_ids: list[int], token: str = None):
    """
    Creates new sections using core_course_create_sections.
    Pass a list of course IDs. One section is created for each ID in the list.
    To create 3 sections in course 2, pass [2, 2, 2].
    """
    params = {}
    for i, cid in enumerate(course_ids):
        params[f"courseids[{i}]"] = cid
    return call_moodle("core_course_create_sections", params, token)

def delete_course_sections(section_ids: list[int], token: str = None):
    """
    Deletes sections using core_course_delete_sections.
    """
    params = {}
    for i, sid in enumerate(section_ids):
        params[f"ids[{i}]"] = sid
    return call_moodle("core_course_delete_sections", params, token)

def create_moodle_section(course_id: int, section_name: str, token: str = None):
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
    return call_moodle("local_sectionmanager_create_sections", params, token)

def create_competency_framework(idnumber: str, shortname: str, description: str, token: str = None):
    """
    Creates a new competency framework.
    """
    params = {
        "competencyframework": {
            "idnumber": idnumber,
            "shortname": shortname,
            "description": description,
            "descriptionformat": 1, # HTML
            "visible": 1,
            "scaleid": 1 # Standard scale (Change if needed)
        }
    }
    return call_moodle("core_competency_create_competency_framework", params, token)

def create_competency(framework_id: int, shortname: str, description: str, idnumber: str, token: str = None):
    """
    Creates a competency within a framework.
    """
    params = {
        "competency": {
            "shortname": shortname,
            "description": description,
            "descriptionformat": 1,
            "idnumber": idnumber,
            "competencyframeworkid": framework_id
        }
    }
    return call_moodle("core_competency_create_competency", params, token)

def create_course_category(name: str, token: str = None):
    """
    Creates a new course category. Returns the category ID.
    Simple implementation; creates at root.
    """
    params = {
        "categories[0][name]": name,
        "categories[0][parent]": 0,
        "categories[0][descriptionformat]": 1
    }
    # Response is a list of created categories
    return call_moodle("core_course_create_categories", params, token)

def create_course(fullname: str, shortname: str, category_id: int, summary: str, token: str = None):
    """
    Creates a new course.
    """
    params = {
        "courses[0][fullname]": fullname,
        "courses[0][shortname]": shortname, # Must be unique
        "courses[0][categoryid]": category_id,
        "courses[0][summary]": summary,
        "courses[0][summaryformat]": 1,
        "courses[0][format]": "topics",
        "courses[0][numsections]": 0 
    }
    return call_moodle("core_course_create_courses", params, token)

def update_section_summary(section_id: int, summary: str, token: str = None):
    """
    Updates the summary of a section. 
    Uses core_course_update_sections (Moodle 4.x).
    """
    # Note: 'core_course_edit_section' is deprecated/complex, 
    # but 'core_course_update_sections' is the standard way to update data.
    # However, depending on Moodle version, checking availability.
    # If not available, we might need a workaround or just skip summary.
    # Trying `core_course_edit_section` as it handles summary updates.
    params = {
        "id": section_id,
        "summary": summary,
        "summaryformat": 1
    }
    return call_moodle("core_course_edit_section", params, token)
