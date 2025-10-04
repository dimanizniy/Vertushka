from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy import create_engine
from core.config import DB_CONFIG

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    import core.models.user
    import core.models.group
    import core.models.station
    Base.metadata.create_all(bind=engine)
