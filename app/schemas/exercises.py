from pydantic import BaseModel


class ExerciseCadence(BaseModel):
    exercise_name: str
    description: str
    typical_months: list[str]
    participating_unit_types: list[str]
    planning_lead_time_days: int
    common_staff_requirements: list[str]
    related_agents: list[str]
    confidence_level: str
    source_required: bool = True
