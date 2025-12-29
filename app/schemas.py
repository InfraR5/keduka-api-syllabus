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
