from pydantic import BaseModel, Field

class GMProgressionPlan(BaseModel):
    content: str = Field(description="The detailed progression plan in markdown format.")
