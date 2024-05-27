from pydantic import BaseModel
from uuid import UUID

class CreateCauseDataClass(BaseModel):
    question_id: UUID
    id: UUID
    row: int
    column: int
    mode: str
    cause: str
    status: bool
    root_status: bool
    feedback: str