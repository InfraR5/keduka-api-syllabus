from typing import List, Optional
from pydantic import BaseModel

class CourseRequest(BaseModel):
    course_id: int

class CourseInfo(BaseModel):
    id: int
    name: str = "Sem Nome"
    description: str = ""

class Competency(BaseModel):
    id: int
    name: str
    description: Optional[str] = ""

class SyllabusResponse(BaseModel):
    course: CourseInfo
    competencies: List[Competency]
    programa: List[str]
