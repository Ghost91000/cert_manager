from sqlalchemy import Column, Integer, String, DateTime, LargeBinary, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB, ARRAY

from datetime import datetime

Base = declarative_base()

# ==================== СВЯЗУЮЩИЕ ТАБЛИЦЫ (Many-to-Many) ====================

# Таблица Certs ↔ PCs
cert_pc_association = Table(
    'cert_pc', Base.metadata,
    Column('pc_id', Integer, ForeignKey('pcs.pc_id', ondelete="CASCADE"), primary_key=True),
    Column('cert_id', Integer, ForeignKey('certs.cert_id', ondelete="CASCADE"), primary_key=True)
)

# Таблица Services ↔ PCs
service_pc_association = Table(
    'service_pc', Base.metadata,
    Column('service_id', Integer, ForeignKey('services.service_id', ondelete="CASCADE"), primary_key=True),
    Column('pc_id', Integer, ForeignKey('pcs.pc_id', ondelete="CASCADE"), primary_key=True)
)

# ==================== ОСНОВНЫЕ ТАБЛИЦЫ ====================

# Таблица для хранения известных пользователей бота
class TelegramUser(Base):
    __tablename__ = "telegram_users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)  # ID в Telegram
    username = Column(String(255), unique=True, nullable=False)  # @username
    chat_id = Column(Integer, nullable=False)  # для отправки сообщений
    is_active = Column(Boolean, nullable=False)


    def __repr__(self):
        return f"<TelegramUser {self.username}>"


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    login = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    tg_alert = Column(String)


class Person(Base):
    __tablename__ = "persons"

    person_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    phone = Column(String)
    email = Column(String)

    # Связи
    cert = relationship("Cert", back_populates="person", cascade="all, delete", passive_deletes=True)


class Cert(Base):
    __tablename__ = "certs"

    cert_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    version = Column(String)
    date_from = Column(DateTime)
    date_to = Column(DateTime)
    thumbprint = Column(String)
    certificate = Column(LargeBinary)
    org = Column(String)

    # Внешние ключи
    person_id = Column(Integer, ForeignKey("persons.person_id", ondelete="SET NULL"), nullable=False)
    # Связи
    person = relationship("Person", back_populates="cert")
    # Связь Many-to-Many с PCs
    pc = relationship("PC", secondary=cert_pc_association, back_populates="cert", cascade="all, delete")

    @property
    def is_active(self):
        """Проверка, активен ли сертификат"""
        today = datetime.now().date()
        return today <= self.date_to.date()

    @property
    def days_until_expiry(self):
        """Дней до истечения срока действия"""
        if not self.Date_to:
            return None
        today = datetime.now().date()
        return (self.Date_to - today).days


class PC(Base):
    __tablename__ = 'pcs'

    pc_id = Column(Integer, primary_key=True, autoincrement=True)
    domain_name = Column(String)

    aud = Column(String)
    email = Column(String)
    phone = Column(String)
    name = Column(String)

    spec = Column(JSONB)
    spec_history = Column(ARRAY(JSONB))

    timestamp = Column(DateTime)

    # Связи Many-to-Many
    cert = relationship("Cert", secondary=cert_pc_association, back_populates="pc", cascade="all, delete")
    service = relationship("Service", secondary=service_pc_association, back_populates="pc", cascade="all, delete")


class Service(Base):
    __tablename__ = 'services'

    service_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    url = Column(String)

    pc = relationship("PC", secondary=service_pc_association, back_populates="service")