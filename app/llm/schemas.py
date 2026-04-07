from typing import Optional, Literal
from pydantic import BaseModel

class Intent(BaseModel):
    action: Literal[
        "create_shift",
        "edit_shift",
        "delete_shift",
        "get_my_schedule",
        "get_my_next_shift",
        "get_my_hours_week",
        "get_my_days_worked_week",
        "list_my_shifts_week",
        "list_my_shifts_next_week"
    ]
    
    employee_name: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    duration_hours: Optional[int] = None
    shift_id: Optional[int] = None