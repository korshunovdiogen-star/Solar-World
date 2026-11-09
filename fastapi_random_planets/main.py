import hashlib
from datetime import date

from database import get_db
from fastapi import Depends, FastAPI, HTTPException
from models import Planet
from sqlalchemy.orm import Session

app = FastAPI()


def get_planet_index(today: date, total_count: int) -> int:
    if total_count <= 0:
        return 0

    date_str = today.isoformat()
    hash_bytes = hashlib.sha256(date_str.encode("utf-8")).digest()
    numeric_hash = int.from_bytes(hash_bytes[:4], "big")
    day_of_year = today.timetuple().tm_yday

    return (numeric_hash + day_of_year) % total_count


@app.get("/planet/today")
def get_todays_planet(db: Session = Depends(get_db)):
    # Берём реальные ID: в базе могут быть пропуски.
    planet_ids = [planet_id for (planet_id,) in db.query(Planet.id).order_by(Planet.id).all()]

    if not planet_ids:
        raise HTTPException(status_code=404, detail="В базе нет планет")

    index = get_planet_index(date.today(), len(planet_ids))
    return {"planet_id": planet_ids[index]}
