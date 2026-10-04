from pydantic import BaseModel

class PPTRequest(BaseModel):
    file_path: str