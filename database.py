from sqlalchemy import create_engine, Column, Integer, String, Date, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import enum
from dotenv import load_dotenv
import os

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URL)
Base = declarative_base()


class Language(enum.Enum):
	UZBEK = "uz"
	RUSSIAN = "ru"


class InstitutionType(enum.Enum):
	BOGCHA_MAKTAB = "bogcha_maktab"
	MARKAZ = "markaz"


class Employee(Base):
	__tablename__ = "employees"
	id = Column(Integer, primary_key=True)
	full_name = Column(String, nullable=False)
	date_of_birth = Column(Date, nullable=False)
	address = Column(String, nullable=False)
	email = Column(String, nullable=False)
	position = Column(String, nullable=False)
	subject = Column(String)
	start_date = Column(Date, nullable=False)
	language = Column(Enum(Language), nullable=False)
	user_phone = Column(String, nullable=False)
	institution_type = Column(Enum(InstitutionType), nullable=False)
	selfie_url = Column(String, nullable=True)


class Student(Base):
	__tablename__ = "students"
	id = Column(Integer, primary_key=True)
	full_name = Column(String, nullable=False)
	date_of_birth = Column(Date, nullable=False)
	age = Column(Integer, nullable=False)
	address = Column(String, nullable=False)
	diagnosis = Column(String, nullable=False)
	attendance_days = Column(String, nullable=False)
	parent_name = Column(String, nullable=False)
	parent_email = Column(String, nullable=False)
	parent_phone = Column(String, nullable=False)
	language = Column(Enum(Language), nullable=False)
	user_phone = Column(String, nullable=False)
	institution_type = Column(Enum(InstitutionType), nullable=False)
	selfie_url = Column(String, nullable=True)


Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
