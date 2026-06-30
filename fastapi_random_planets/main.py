from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from datetime import date
import hashlib
from database import get_db, engine
from models import Planet, Base
 
app = FastAPI()
 
def get_planet_index(today: date, total_count: int) -> int:
    date_str = today.isoformat()
    hash_bytes = hashlib.sha256(date_str.encode('utf-8')).digest()
    numeric_hash = int.from_bytes(hash_bytes[:4], 'big')
    return numeric_hash % total_count
 
@app.get("/planet/today")
def get_todays_planet():
    today = date.today()
    day_of_year = today.timetuple().tm_yday  # число от 1 до 366
    date_str = today.isoformat()
    hash_bytes = hashlib.sha256(date_str.encode('utf-8')).digest()
    numeric_hash = int.from_bytes(hash_bytes[:4], 'big')
    # Добавляем день года, чтобы сдвигать результат
    index = (numeric_hash + day_of_year) % 8
    return {"planet_id": index}