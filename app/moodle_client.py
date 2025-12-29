import requests
from typing import List, Dict, Any, Optional
from .config import settings
from .schemas import CourseInfo, Competency

class MoodleClient:
    def __init__(self):
        self.base_url = settings.moodle_url
        self.token = settings.moodle_token
        self.endpoint = f"{self.base_url}/webservice/rest/server.php"

    def _call_moodle(self, function_name: str, params: Dict[str, Any] = None) -> Any:
        full_params = {
            "wstoken": self.token,
            "wsfunction": function_name,
            "moodlewsrestformat": "json",
        }
        if params:
            full_params.update(params)

        try:
            response = requests.post(self.endpoint, data=full_params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "exception" in data:
                # Basic error handling for Moodle exceptions
                print(f"Moodle Error: {data['exception']} - {data.get('message', '')}")
                return None
                
            return data
        except requests.RequestException as e:
            print(f"Request Error: {e}")
            return None

    def get_course_details(self, course_id: int) -> Optional[CourseInfo]:
        """
        Fetches course details using core_course_get_courses
        """
        params = {"options[ids][0]": course_id}
        data = self._call_moodle("core_course_get_courses", params)
        
        if not data or not isinstance(data, list) or len(data) == 0:
            return None
            
        course_data = data[0]
        # Handle cases where summary/name might be missing or different
        return CourseInfo(
            id=course_data.get("id"),
            name=course_data.get("fullname", "Sem Nome"),
            description=course_data.get("summary", "")
        )

    def get_course_competencies(self, course_id: int) -> List[Competency]:
        """
        Fetches competencies using core_competency_list_course_competencies
        """
        params = {"id": course_id}
        data = self._call_moodle("core_competency_list_course_competencies", params)
        
        competencies = []
        if data and isinstance(data, list):
             # Moodle often returns a list of dictionaries directly for this call
             # Structure might vary slightly by version, but typically it sends the list directly.
             # Wait, core_competency_list_course_competencies usually returns a list of objects.
             for item in data:
                 # Check if the structure is wrapped or direct
                 comp_data = item.get('competency', item) 
                 
                 competencies.append(Competency(
                     id=comp_data.get('id', 0),
                     name=comp_data.get('shortname') or comp_data.get('idnumber', 'Competência'),
                     description=comp_data.get('description', '')
                 ))
                 
        return competencies

    def generate_syllabus(self, course_info: CourseInfo, competencies: List[Competency]) -> List[str]:
        """
        Generates a syllabus based on competencies or falls back to default logic.
        """
        if competencies:
            # If competencies exist, use them as topics
            return [f"Módulo: {comp.name}" for comp in competencies]
        
        # Fallback if no competencies found
        # In a real scenario, we might parse the course description or sections.
        # For now, we return a standard generic structure as per requirements.
        return [
            "Introdução e Fundamentos",
            "Desenvolvimento e Prática",
            "Avaliação Final"
        ]
