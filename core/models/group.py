from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from core.models import Base

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    score = Column(Integer, default=0)

    users = relationship("User", back_populates="group")

    def __repr__(self):
        return f"<Group id={self.id} name={self.name} score={self.score}>"
