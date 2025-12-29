from fastapi import FastAPI, HTTPException, Depends
from .schemas import CourseRequest, SyllabusResponse
from .moodle_client import MoodleClient

app = FastAPI(title="Moodle Syllabus API", version="1.0.0")

def get_moodle_client():
    return MoodleClient()

@app.post("/api/course/programa", response_model=SyllabusResponse)
async def generate_course_syllabus(
    request: CourseRequest,
    client: MoodleClient = Depends(get_moodle_client)
):
    """
    Generates a syllabus for a given Moodle course ID.
    """
    
    # 1. Fetch Course Details
    course_info = client.get_course_details(request.course_id)
    if not course_info:
        raise HTTPException(status_code=404, detail="Curso não encontrado no Moodle")
        
    # 2. Fetch Competencies
    competencies = client.get_course_competencies(request.course_id)
    
    # 3. Generate Syllabus Program
    program_list = client.generate_syllabus(course_info, competencies)
    
    return SyllabusResponse(
        course=course_info,
        competencies=competencies,
        programa=program_list
    )

@app.get("/health")
def health_check():
    return {"status": "ok"}
