from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from datetime import datetime

Base = declarative_base()

# ==================== СВЯЗУЮЩИЕ ТАБЛИЦЫ (Many-to-Many) ====================

# Таблица Certs ↔ PCs
cert_pc_association = Table(
    'cert_pc', Base.metadata,
    Column('pc_id', Integer, ForeignKey('pcs.pc_id'), primary_key=True),
    Column('cert_id', Integer, ForeignKey('certs.cert_id'), primary_key=True)
)

# Таблица Services ↔ PCs
service_pc_association = Table(
    'service_pc', Base.metadata,
    Column('service_id', Integer, ForeignKey('services.service_id'), primary_key=True),
    Column('pc_id', Integer, ForeignKey('pcs.pc_id'), primary_key=True)
)

# ==================== ОСНОВНЫЕ ТАБЛИЦЫ ====================

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

    # Внешние ключи
    person_id = Column(Integer, ForeignKey("persons.person_id", ondelete="SET NULL"), nullable=False)
    org_id = Column(Integer, ForeignKey("orgs.org_id", ondelete="SET NULL"), nullable=False)
    # Связи
    person = relationship("Person", back_populates="cert")
    org = relationship("Org", back_populates="cert")
    # Связь Many-to-Many с PCs
    pc = relationship("PC", secondary=cert_pc_association, back_populates="cert")

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


class Org(Base):
    __tablename__ = "orgs"

    org_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    url = Column(String)

    # Связи
    cert = relationship("Cert", back_populates="org", cascade="all, delete-orphan", passive_deletes=True)


class PC(Base):
    __tablename__ = 'pcs'

    pc_id = Column(Integer, primary_key=True, autoincrement=True)
    domain_name = Column(String)
    aud = Column(String)
    email = Column(String)
    phone = Column(String)
    name = Column(String)

    # Связи Many-to-Many
    cert = relationship("Cert", secondary=cert_pc_association, back_populates="pc")
    service = relationship("Service", secondary=service_pc_association, back_populates="pc")


class Service(Base):
    __tablename__ = 'services'

    service_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    url = Column(String)

    pc = relationship("PC", secondary=service_pc_association, back_populates="service")