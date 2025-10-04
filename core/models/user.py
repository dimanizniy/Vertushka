from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from core.models import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tg_id = Column(Integer, unique=True, index=True, nullable=False)
    role = Column(String, nullable=False, default="player")  # player | curator | organizer | admin
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)

    group = relationship("Group", back_populates="users")

    def __repr__(self):
        return f"<User id={self.id} tg_id={self.tg_id} role={self.role}>"
