from typing import List, Optional
from pydantic import BaseModel

class CourseRequest(BaseModel):
    course_id: int

class Competency(BaseModel):
    id: int
    name: str
    description: Optional[str] = ""

class ProgramResponse(BaseModel):
    course: dict
    competencies: List[Competency]
    programa: List[str]

class CreateSectionRequest(BaseModel):
    course_id: int
    name: str

class DeleteSectionRequest(BaseModel):
    section_ids: List[int]

class CreateBulkSectionsRequest(BaseModel):
    course_id: int
    names: List[str]

# --- Agent Models ---

class AgentInput(BaseModel):
    objetivo: str
    publico: str
    nivel: str

class MoodleModule(BaseModel):
    name: str
    content: str
    activity: str
    evaluation: str

class MoodleCourseStructure(BaseModel):
    name: str
    objective: str
    workload: int
    modules: List[MoodleModule]

class CompetencyDetail(BaseModel):
    name: str
    description: str
    level: str
    id_technical: str

class AgentOutput(BaseModel):
    competency: CompetencyDetail
    structure: List[str]
    courses: List[MoodleCourseStructure]
    evaluation_rules: dict
