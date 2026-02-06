from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Подключение к БД
DATABASE_URL = "postgresql://postgres:12345678@localhost/cert"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()