from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Planet(Base):
    __tablename__ = "planets_planet"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(20), nullable=False)
    order = Column(Integer, nullable=False)
    planet_type = Column(String(3), nullable=False)
    radius = Column(Float, nullable=False)
    text = Column(Text, nullable=True)
    image = Column(String, nullable=True)
    satellites = relationship("Satellite", back_populates="planet")



class Satellite(Base):
    __tablename__ = "planets_satellite"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    radius = Column(Float, nullable=True)
    planet_id = Column(Integer, ForeignKey("planets_planet.id"), nullable=False)
    planet = relationship("Planet", back_populates="satellites")