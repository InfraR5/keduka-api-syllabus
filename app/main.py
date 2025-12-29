from fastapi import FastAPI, HTTPException
from .schemas import CourseRequest, ProgramResponse
from .moodle_client import call_moodle

app = FastAPI(title="Course Program API")

@app.post("/api/course/programa", response_model=ProgramResponse)
def gerar_programa(data: CourseRequest):

    # 1. Dados do curso
    course = call_moodle(
        "core_course_get_courses",
        {"options[ids][0]": data.course_id}
    )

    if not course:
        raise HTTPException(404, "Curso não encontrado")

    course_data = course[0]

    # 2. Competências do curso
    competencies = call_moodle(
        "core_competency_list_course_competencies",
        {"courseid": data.course_id}
    )

    # 3. Geração simples do conteúdo programático
    programa = []

    # Safe iteration over competencies since Moodle might return various shapes, 
    # but we assume the standard User snippet structure.
    # Note: Moodle's core_competency_list_course_competencies returns a list of objects 
    # where each has a "competency" key.
    if isinstance(competencies, list):
        for comp in competencies:
            if "competency" in comp and "shortname" in comp["competency"]:
                programa.append(comp["competency"]["shortname"])

    # fallback caso não haja competências
    if not programa:
        programa = [
            "Introdução ao curso",
            "Conceitos fundamentais",
            "Aplicações práticas",
            "Avaliação final"
        ]

    # Formatting competencies for response
    formatted_competencies = []
    if isinstance(competencies, list):
        for c in competencies:
            if "competency" in c:
                formatted_competencies.append({
                    "id": c["competency"]["id"],
                    "name": c["competency"]["shortname"],
                    "description": c["competency"].get("description", "")
                })

    return {
        "course": {
            "id": course_data.get("id"),
            "name": course_data.get("fullname"),
            "description": course_data.get("summary", "")
        },
        "competencies": formatted_competencies,
        "programa": programa
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}
