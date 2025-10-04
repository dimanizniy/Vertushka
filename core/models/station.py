from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from core.models import Base

class Station(Base):
    __tablename__ = "stations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    curator_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    curator = relationship("User", backref="station")

    def __repr__(self):
        return f"<Station id={self.id} name={self.name}>"
