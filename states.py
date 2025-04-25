from aiogram.fsm.state import StatesGroup, State


class SurveyTypeForm(StatesGroup):
	language = State()
	institution_type = State()  # New state for Bog‘cha/Maktab or Markaz
	user_phone = State()
	survey_type = State()


class EmployeeForm(StatesGroup):
	full_name = State()
	date_of_birth = State()
	address = State()
	email = State()
	position = State()
	start_date = State()


class StudentForm(StatesGroup):
	full_name = State()
	date_of_birth = State()
	age = State()
	address = State()
	diagnosis = State()
	attendance_days = State()
	parent_name = State()
	parent_email = State()
	parent_phone = State()
