from fastapi import FastAPI, HTTPException
from .schemas import CourseRequest, ProgramResponse, CreateSectionRequest, DeleteSectionRequest
from .moodle_client import call_moodle, create_moodle_section, delete_course_sections
from .ai_service import generate_syllabus_ai

app = FastAPI(
    title="Course Program API",
    docs_url="/api/course/program/docs",
    openapi_url="/api/course/program/openapi.json"
)

@app.post("/api/course/program/sections/create")
def create_section_endpoint(data: CreateSectionRequest):
    try:
        result = create_moodle_section(data.course_id, data.name)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/course/program/sections/delete")
def delete_sections_endpoint(data: DeleteSectionRequest):
    try:
        # Assuming delete_course_sections returns something useful or throws
        result = delete_course_sections(data.section_ids)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/course/programa", response_model=ProgramResponse)
def gerar_programa(data: CourseRequest):

    # 1. Dados do curso
    try:
        # 1. Dados do curso
        course = call_moodle(
            "core_course_get_courses",
            {"options[ids][0]": data.course_id}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not course or (isinstance(course, list) and len(course) == 0):
        # Fallback debug info or 404
        raise HTTPException(404, "Curso não encontrado (Resposta vazia do Moodle)")
    
    # Handle case where call_moodle returns dict (already handled by exception above, but safety check)
    if isinstance(course, dict):
         # If Moodle returns a single object implies error was missed or structure changed
         raise HTTPException(500, f"Formato de resposta inesperado do Moodle: {course}")

    course_data = course[0]

    # 2. Competências do curso
    competencies = call_moodle(
        "core_competency_list_course_competencies",
        {"id": data.course_id}
    )

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

    # 3. Geração de conteúdo programático (IA)
    programa = generate_syllabus_ai(
        course_name=course_data.get("fullname", "Curso sem nome"),
        course_desc=course_data.get("summary", ""),
        competencies=formatted_competencies
    )

    # fallback se a IA falhar ou retornar vazio
    if not programa:
        # Fallback para competências se não houver programa gerado
        if isinstance(competencies, list):
             for comp in competencies:
                if "competency" in comp and "shortname" in comp["competency"]:
                    programa.append(comp["competency"]["shortname"])
        
        # Fallback final se nem competências existirem
        if not programa:
            programa = [
                "Introdução ao curso",
                "Conceitos fundamentais",
                "Aplicações práticas",
                "Avaliação final"
            ]

    # 4. Gravar no Moodle (Persistence) via Sections
    apply_syllabus_structure(data.course_id, programa)

    return {
        "course": {
            "id": course_data.get("id"),
            "name": course_data.get("fullname"),
            "description": course_data.get("summary", "")
        },
        "competencies": formatted_competencies,
        "programa": programa
    }

def apply_syllabus_structure(course_id: int, programa: list[str]):
    """
    Updates course sections to match the generated syllabus using local_sectionmanager.
    REV 18 - ROBUST PLUGIN IMPLEMENTATION
    """
    from .moodle_client import get_course_contents, update_section_name, create_moodle_section, delete_course_sections

    try:
        print("[AI SERVICE] VERSION: REV 18 - LOCAL PLUGIN POWERED")
        print(f"[AI SERVICE] Fetching sections for course {course_id}...")
        sections = get_course_contents(course_id)
        
        # Filter only real sections (exclude Section 0 'General')
        real_sections = [s for s in sections if s.get("section", 0) != 0]
        current_count = len(real_sections)
        
        print(f"[AI SERVICE] Current Sections: {current_count}")
        print(f"[AI SERVICE] Syllabus Items: {len(programa)}")

        # 1. Update Existing Sections
        # We iterate through existing sections and rename them to match the syllabus topics.
        limit = min(current_count, len(programa))
        for i in range(limit):
            topic = programa[i]
            sec_id = real_sections[i]["id"]
            print(f"[AI SERVICE] Updating Section {sec_id} -> {topic}")
            update_section_name(sec_id, topic)

        # 2. Create New Sections (if needed)
        if len(programa) > current_count:
            diff = len(programa) - current_count
            print(f"[AI SERVICE] Creating {diff} new sections via Plugin...")
            
            for i in range(current_count, len(programa)):
                topic_name = programa[i]
                print(f"[AI SERVICE] Creating new section: '{topic_name}'")
                create_moodle_section(course_id, topic_name)

        # 3. Delete Excess Sections (if needed)
        elif current_count > len(programa):
            diff = current_count - len(programa)
            print(f"[AI SERVICE] Deleting {diff} excess sections...")
            
            to_delete = real_sections[len(programa):]
            ids_to_delete = [s["id"] for s in to_delete]
            
            print(f"[AI SERVICE] Deleting Section IDs: {ids_to_delete}")
            delete_course_sections(ids_to_delete)

        print("[AI SERVICE] Course structure updated successfully (Plugin Hybrid Strategy).")

    except Exception as e:
        print(f"[AI SERVICE] Failed to update course structure: {e}")
