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

@app.get("/health")
def health_check():
    return {"status": "ok"}


# --- AGENT ORCHESTRATION ---

from .schemas import AgentInput, AgentOutput
from .ai_service import generate_full_structure
from .moodle_client import (
    create_competency_framework, 
    create_competency, 
    create_course_category, 
    create_course, 
    create_moodle_section, 
    update_section_summary
)
import random

@app.post("/api/agent/generate", response_model=AgentOutput)
def generate_competency_framework(data: AgentInput):
    """
    Orchestrates the creation of a full educational structure in Moodle.
    """
    print(f"[AGENT] Received request: {data}")

    # 1. AI Generation
    try:
        structure = generate_full_structure(data.objetivo, data.publico, data.nivel)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Generation failed: {str(e)}")

    # 2. Moodle Execution
    try:
        # A. Competency Framework & Competency
        # Create a category unique for this request or generalized?
        # For simplicity, creating a Framework per execution or reusing if ID known?
        # The AI generates a technical ID. We can use that as IDNumber.
        
        comp_data = structure.competency
        
        # Create Framework (One per competency for isolation in this MVP)
        fw_idnumber = f"FW_{comp_data.id_technical}_{random.randint(1000,9999)}"
        print(f"[AGENT] Creating Framework: {fw_idnumber}")
        
        fw_res = create_competency_framework(
            idnumber=fw_idnumber,
            shortname=f"Framework - {comp_data.name}",
            description=f"Automated framework for {comp_data.name}"
        )
        fw_id = fw_res["id"]

        # Create Competency
        print(f"[AGENT] Creating Competency in Framework {fw_id}")
        comp_res = create_competency(
            framework_id=fw_id,
            shortname=comp_data.name,
            description=comp_data.description,
            idnumber=comp_data.id_technical
        )
        # comp_resid = comp_res["id"]

        # B. Courses
        # Create a Category for these courses?
        cat_res = create_course_category(name=f"Program: {comp_data.name}")
        cat_id = cat_res[0]["id"]
        
        # Create Courses
        for course in structure.courses:
            shortname = f"{course.name[:20].strip()}_{random.randint(100,999)}"
            print(f"[AGENT] Creating Course: {course.name} ({shortname})")
            
            c_res = create_course(
                fullname=course.name,
                shortname=shortname,
                category_id=cat_id,
                summary=course.objective
            )
            c_id = c_res[0]["id"]
            
            # C. Sections (Modules)
            # Moodle creates section 0 by default. 
            # We create NEW sections for modules.
            for module in course.modules:
                print(f"[AGENT] Creating Module: {module.name} in Course {c_id}")
                sec_res = create_moodle_section(c_id, module.name)
                
                # The response from create_moodle_section might vary depending on plugin version.
                # Assuming it returns a list of created sections or the section object.
                # local_sectionmanager returns the list of CREATED sections.
                if isinstance(sec_res, list) and len(sec_res) > 0:
                    sec_id = sec_res[0]["id"]
                    
                    # Update Summary (Content)
                    content_html = f"""
                    <div class="agent-module-content">
                        <h3>Conteúdo</h3>
                        <p>{module.content}</p>
                        <hr>
                        <h3>Atividade Prática</h3>
                        <p>{module.activity}</p>
                        <hr>
                        <p><strong>Avaliação:</strong> {module.evaluation}</p>
                    </div>
                    """
                    update_section_summary(sec_id, content_html)
                    
    except Exception as e:
        # In a real agent, we might want to rollback. Here we just report.
        print(f"[AGENT] Moodle Execution Partial Failure: {str(e)}")
        # We still return the structure so the user sees what WAS generated/attempted.
        # But maybe we should insert a warning in the response?
        # For now, just logging.
        pass

    return structure
