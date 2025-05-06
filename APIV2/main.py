from fastapi import FastAPI, HTTPException, Path, Query, Body, Depends, UploadFile, File
from typing import Optional, Annotated, List
from sqlalchemy.orm import Session
from models import Base, RawData, SystemInfo, CriticalPoint
from database import engine, session_local
from schemas import RawDataRequest, SystemInfoResponse, RawDataUpdate, CriticalPointCreate, CriticalPointResponse, SystemInfoUpdate
from datetime import datetime
import pandas as pd
import json
from sqlalchemy import func

app = FastAPI()
Base.metadata.create_all(bind=engine)

def get_db():
    db = session_local()
    try:
        yield db
    finally:
        db.close()

@app.get("/get-system-info/{id_raw}", response_model=dict)
async def get_system_info(id_raw: int, db: Session = Depends(get_db)):
    # Получение данных для конкретного id_raw
    system_info = db.query(SystemInfo).filter(SystemInfo.id_raw == id_raw).all()

    if not system_info:
        raise HTTPException(status_code=404, detail="System info not found")

    # Преобразование данных в словарь
    system_info_dict = {}
    for item in system_info:
        system_info_dict[item.param] = item.value

    return system_info_dict

# Работает
def update_pc_to_table(input_id: int, data: dict, db: Session):
    id_raw = input_id
    if id_raw is None:
        raise ValueError("id_raw is required in the data")

    # Проверяем, есть ли host в новых данных
    new_host = data.get("host", None)

    if not new_host:
        # Если host отсутствует, берём его из БД перед удалением старых записей
        existing_host = db.query(SystemInfo.host).filter(SystemInfo.id_raw == id_raw).first()
        if existing_host:
            new_host = existing_host[0]  # Получаем строку host

    print(f"Пришли данные: {data}")  # Проверка данных

    # Удаляем старые записи
    db.query(SystemInfo).filter(SystemInfo.id_raw == id_raw).delete()

    # Добавляем новые записи
    for param, value in data.items():
        if param == "id_raw" or param == "host":
            continue  # Пропускаем служебные поля
        if isinstance(value, list):
            value = str(value)

        print(f"Добавляем параметр {param}: {value}")  # Проверка добавления

        sys_info = SystemInfo(id_raw=id_raw, host=new_host, param=param, value=value)
        db.add(sys_info)

    db.commit()



# Работает
@app.put("/update-pc/{id_raw}", response_model=dict)
async def update_pc(id_raw: int, data: dict = Body(...), db: Session = Depends(get_db)):
    try:
        updated_data = data.get("data", {})
        params_to_delete = data.get("params_to_delete", [])

        # Удаление конкретных параметров перед обновлением
        if params_to_delete:
            db.query(SystemInfo).filter(SystemInfo.id_raw == id_raw, SystemInfo.param.in_(params_to_delete)).delete()

        update_pc_to_table(id_raw, updated_data, db)
        return {"message": f"PC with id_raw {id_raw} updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.delete("/delete-data/{id_raw}")
async def delete_data(id_raw: Annotated[int, Path(..., title="Укажите имя host")],
                      db: Session = Depends(get_db)):
    params = db.query(SystemInfo).filter(SystemInfo.id_raw == id_raw).all()
    if not params:
        raise HTTPException(status_code=404, detail="Такого  в таблице system-info не найдено")
    for param in params:
        db.delete(param)

    db.commit()
    return{"massage": f'Удаление успешно завершено'}

# Работает
@app.get("/get-actual-system-info/", response_model=List[SystemInfoResponse])
async def get_actual_system_info(db: Session = Depends(get_db)):
    try:
        # Подзапрос для выбора максимального id_raw для каждого host
        subquery = (
            db.query(
                SystemInfo.host,
                func.max(SystemInfo.id_raw).label("max_id_raw")
            )
            .group_by(SystemInfo.host)
            .subquery()
        )

        # Основной запрос для выбора актуальных записей
        actual_system_info = (
            db.query(SystemInfo)
            .join(
                subquery,
                (SystemInfo.host == subquery.c.host) & (SystemInfo.id_raw == subquery.c.max_id_raw)
            )
            .all()
        )

        return actual_system_info

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# Работает
@app.post("/post-data/")
async def create_raw_data(raw_data: RawDataRequest, db: Session = Depends(get_db)):
    for item_data in raw_data.data:
        host = item_data.get('host')
        db_raw_data = RawData(host=host,data=item_data, time_date = datetime.now())
        db.add(db_raw_data)
        db.commit()
        db.refresh(db_raw_data)

        distribution_to_table(db_raw_data.data, db_raw_data.id, db)

    return {"massage": "Post успешно завершен"}

# Изменить
@app.put("/update-data/{host}")
async def update_raw_data(host: Annotated[str, Path(..., title="Укажите имя host")],
                          updated_data: RawDataUpdate,
                          db: Session = Depends(get_db)):
    # Поиск существующей записи в таблице RawData
    db_raw_data = db.query(RawData).filter(RawData.host == host).first()
    if not db_raw_data:
        raise HTTPException(status_code=404, detail="Такой host не найден")

    # Обновление данных
    db_raw_data.data = updated_data.data
    db_raw_data.time_date = datetime.now()

    db.commit()
    db.refresh(db_raw_data)

    # Обновление данных в таблице SystemInfo
    update_to_table(db_raw_data.data, db)

    return {"message": f"Данные ПК {host} успешно обновлены"}

# Работает
def update_to_table(data: dict, db: Session):
    host = data.get("host")
    # Удаление старых записей для данного host
    db.query(SystemInfo).filter(SystemInfo.host == host).delete()

    # Добавление новых записей
    for param, value in data.items():
        if isinstance(value, list):
            value = str(value)
        sys_info = SystemInfo(host=host, param=param, value=value)
        db.add(sys_info)
    db.commit()

# Работает
#Производит пересон данных в таблицу system_info
def distribution_to_table(data: dict, id: int, db: Session):
    host = data.get("host")
    id_raw = id
    
    for param, value in data.items():
            if isinstance(value, (str, int, float)):  # Простые значения
                sys_entry = SystemInfo(id_raw=id_raw, host=host, param=param, value=str(value))
                db.add(sys_entry)
            elif isinstance(value, list):  # Массивы - записываем каждый элемент отдельно
                for item in value:
                    sys_entry = SystemInfo(id_raw=id_raw, host=host, param=param, value=str(item))
                    db.add(sys_entry)
    
    db.commit()

@app.get("/get-data/{host}", response_model=List[SystemInfoResponse])
async def get_data(host: Annotated[str, Path(..., title="Укажите имя host")],
                   db: Session = Depends(get_db)):
    params = db.query(SystemInfo).filter(SystemInfo.host == host).all()
    return params

# Работает
@app.get("/get-filtered-system-info/", response_model=List[SystemInfoResponse])
async def get_filtred_info(hosts: Optional[List[str]] = Query(default = None, title='Укажите host для фильтрации'),
                           params: Optional[List[str]] = Query(default = None, title='Укажите host для фильтрации'),
                           values: Optional[List[str]] = Query(default = None, title='Укажите host для фильтрации'),
                            start_date: Optional[datetime] = Query(default=None, title='Начальная дата для фильтрации'),
                            end_date: Optional[datetime] = Query(default=None, title='Конечная дата для фильтрации'),
                           db: Session = Depends(get_db)):
    query = db.query(SystemInfo)
    if hosts:
        query = query.filter(SystemInfo.host.in_(hosts))
    
    if params:
        query = query.filter(SystemInfo.param.in_(params))

    if values:
        query = query.filter(SystemInfo.value.in_(values))

    if start_date:
        query = query.filter(SystemInfo.time_date >= start_date)

    if end_date:
        query = query.filter(SystemInfo.time_date <= end_date)

    return query.all()

# Работает
@app.delete("/delete-all-data/")
async def delete_all_data(db: Session = Depends(get_db)):
    try:
        # Удаление всех записей из таблицы SystemInfo
        db.query(SystemInfo).delete()

        # Удаление всех записей из таблицы RawData
        db.query(RawData).delete()

        # Подтверждение изменений в базе данных
        db.commit()

        return {"message": "Все данные успешно удалены"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении данных: {str(e)}")

# Работает
@app.post("/upload-excel/")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    df = pd.read_excel(file.file, dtype=str)
    failed_rows = []

    for _, row in df.iterrows():
        json_data = row.get("JSON", "{}")

        if not isinstance(json_data, str):
            json_data = "{}"

        try:
            parsed_data = json.loads(json_data)
        except json.JSONDecodeError as e:
            failed_rows.append({"JSON": json_data, "error": str(e)})
            continue

        host = parsed_data.get("host", "unknown")

        # Записываем в raw_data
        raw_entry = RawData(host=host, data=parsed_data, time_date = datetime.now())
        db.add(raw_entry)
        db.commit()
        db.refresh(raw_entry)
        distribution_to_table(raw_entry.data, raw_entry.id, db)


        db.commit()

    if failed_rows:
        failed_df = pd.DataFrame(failed_rows)
        failed_df.to_csv("failed_rows.csv", index=False)

    return {"message": "File processed successfully", "failed_rows": len(failed_rows)}

# Работает
@app.post("/critical-points/", response_model=CriticalPointResponse)
def create_critical_point(critical_point: CriticalPointCreate, db: Session = Depends(get_db)):
    db_critical_point = CriticalPoint(**critical_point.dict())
    db.add(db_critical_point)
    db.commit()
    db.refresh(db_critical_point)
    return db_critical_point

# Работает
@app.get("/critical-points/", response_model=List[CriticalPointResponse])
def read_critical_points(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(CriticalPoint).offset(skip).limit(limit).all()

# Работает
@app.put("/critical-points/{param}", response_model=CriticalPointResponse)
def update_critical_point(param: Annotated[str, Path(..., title="Укажите param")],
                          critical_point: CriticalPointCreate,
                          db: Session = Depends(get_db)):
    db_critical_point = db.query(CriticalPoint).filter(CriticalPoint.param == param).first()
    if db_critical_point is None:
        raise HTTPException(status_code=404, detail="Critical point not found")

    for key, value in critical_point.dict(exclude_unset=True).items():
        setattr(db_critical_point, key, value)

    db.commit()
    db.refresh(db_critical_point)
    return db_critical_point

# Работает
@app.delete("/critical-points/{param}")
async def delete_critical_point(param: Annotated[str, Path(..., title="Укажите param")],
                                db: Session = Depends(get_db)):
    del_param = db.query(CriticalPoint).filter(CriticalPoint.param == param).first()
    if not del_param:
        raise HTTPException(status_code=404, detail="Такого param не найдено. Возможно его стоит добавить в список критических точек")

    db.delete(del_param)
    db.commit()
    return {"massage": f'Удаление итической точки "{param}" успешно завершено'}