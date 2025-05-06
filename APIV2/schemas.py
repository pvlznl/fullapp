from pydantic import BaseModel
from typing import List, Optional,Dict,Any
from datetime import datetime


class SystemInfoUpdate(BaseModel):
    data: Dict[str, Any]

class RawDataRequest(BaseModel):
    data: List[dict]

class SystemInfoResponse(BaseModel):
    id: int
    id_raw: int
    host: str
    param: str
    value: str
    time_date: datetime

    class Config:
        orm_mode = True


class RawDataUpdate(BaseModel):
    data: dict

class CriticalPointCreate(BaseModel):
    param: str
    check_type: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    exact_value: Optional[float] = None
    measure_of_calculation: Optional[str] = None
    day_count: Optional[int] = None
    string_value: Optional[str] = None

class CriticalPointResponse(BaseModel):
    param: str
    check_type: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    exact_value: Optional[float] = None
    measure_of_calculation: Optional[str] = None
    day_count: Optional[int] = None
    string_value: Optional[str] = None

    class Config:
        orm_mode = True