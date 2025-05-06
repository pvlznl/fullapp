from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime, Float
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy.sql import func
from typing import List, Dict

class RawData(Base):
    __tablename__ = "raw_data" #Название таблицы

    id = Column(Integer, primary_key=True, index=True)
    host = Column(String, index=True)
    data = Column(JSON)
    time_date = Column(DateTime(timezone=True), server_default=func.now())

class SystemInfo(Base):
    __tablename__ = "system_info"  # Название таблицы

    id = Column(Integer, primary_key=True, index=True)
    id_raw = Column(Integer, index=True)
    host = Column(String, index=True)
    param = Column(String, index=True)
    value = Column(String, index=True)
    time_date = Column(DateTime(timezone=True), server_default=func.now())


from datetime import datetime
class CriticalPoint(Base):
    __tablename__ = "critical_points"
    
    param = Column(String, primary_key=True, index=True)
    check_type = Column(String, nullable=True) 
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    exact_value = Column(Float, nullable=True)
    measure_of_calculation = Column(String, nullable=True)
    day_count = Column(Integer, nullable=True)
    string_value = Column(String, nullable=True)