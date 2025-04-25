import asyncio
import re
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, KeyboardButton, \
	ReplyKeyboardMarkup
from dotenv import load_dotenv
import os
from database import SessionLocal, Employee, Student, Language, InstitutionType
from states import SurveyTypeForm, EmployeeForm, StudentForm
from keyboard import get_language_keyboard, get_survey_type_keyboard, get_contact_keyboard, \
	get_institution_type_keyboard
from datetime import datetime

logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

load_dotenv()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
PHONE_REGEX = r'^\+?\d{10,15}$'


@dp.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
	logger.info(f"User {message.from_user.id} started bot with /start")
	await state.clear()

	if message.from_user.id == ADMIN_ID:
		keyboard = [[KeyboardButton(text="Javoblar / Ответы")]]
		reply_markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)
		await message.answer(
			"Javoblarni ko‘rish uchun tugmani bosing / Нажмите кнопку для просмотра ответов:",
			reply_markup=reply_markup
		)
	else:
		reply_markup = get_language_keyboard()
		await message.answer(
			"Iltimos, tilni tanlang / Пожалуйста, выберите язык:",
			reply_markup=reply_markup
		)
		await state.set_state(SurveyTypeForm.language)


@dp.message(F.text == "Javoblar / Ответы")
async def handle_responses_button(message: Message, state: FSMContext):
	if message.from_user.id != ADMIN_ID:
		logger.warning(f"Unauthorized access to Responses by user {message.from_user.id}")
		await message.answer("Sizda admin huquqlari yo‘q / У вас нет прав администратора.")
		return

	logger.info(f"Admin {message.from_user.id} clicked Responses button")
	lang = "uz"

	with SessionLocal() as session:
		employees = session.query(Employee.user_phone, Employee.full_name).distinct(Employee.user_phone).all()
		students = session.query(Student.user_phone, Student.full_name).distinct(Student.user_phone).all()
		users = {phone: name for phone, name in employees + students}

	if not users:
		logger.info(f"Admin {message.from_user.id} found no responses")
		await message.answer("Hech qanday javob topilmadi / Ответы не найдены")
		return

	keyboard = InlineKeyboardMarkup(inline_keyboard=[
		[InlineKeyboardButton(text=f"{name} ({phone})", callback_data=f"user_{phone}")]
		for phone, name in users.items()
	])
	await message.answer("Foydalanuvchilarni tanlang / Выберите пользователя:", reply_markup=keyboard)


@dp.callback_query()
async def handle_callback_query(callback: CallbackQuery):
	if callback.from_user.id != ADMIN_ID:
		logger.warning(f"Unauthorized callback access by user {callback.from_user.id}")
		await callback.answer("Sizda admin huquqlari yo‘q / У вас нет прав администратора.", show_alert=True)
		return

	data = callback.data
	logger.info(f"Admin {callback.from_user.id} triggered callback: {data}")
	lang = "uz"

	if data == "show_responses":
		with SessionLocal() as session:
			employees = session.query(Employee.user_phone, Employee.full_name).distinct(Employee.user_phone).all()
			students = session.query(Student.user_phone, Student.full_name).distinct(Student.user_phone).all()
			users = {phone: name for phone, name in employees + students}

		if not users:
			logger.info(f"Admin {callback.from_user.id} found no responses")
			await callback.message.edit_text("Hech qanday javob topilmadi / Ответы не найдены")
			await callback.answer()
			return

		keyboard = InlineKeyboardMarkup(inline_keyboard=[
			[InlineKeyboardButton(text=f"{name} ({phone})", callback_data=f"user_{phone}")]
			for phone, name in users.items()
		])
		await callback.message.edit_text("Foydalanuvchilarni tanlang / Выберите пользователя:", reply_markup=keyboard)
		await callback.answer()

	elif data.startswith("user_"):
		user_phone = data[len("user_"):]
		logger.info(f"Admin {callback.from_user.id} selected user with phone: {user_phone}")

		with SessionLocal() as session:
			employees = session.query(Employee).filter_by(user_phone=user_phone).all()
			students = session.query(Student).filter_by(user_phone=user_phone).all()

		if not (employees or students):
			logger.info(f"Admin {callback.from_user.id} found no responses for user_phone: {user_phone}")
			await callback.message.edit_text(
				"Bu foydalanuvchi uchun javoblar topilmadi / Ответы для этого пользователя не найдены")
			await callback.answer()
			return

		response_text = f"Foydalanuvchi: {user_phone}\n\n"
		if employees:
			response_text += "Xodimlar / Сотрудники:\n"
			for emp in employees:
				response_text += (
					f"- Ism: {emp.full_name}\n"
					f"  Muassasa turi: Bog‘cha / Maktab\n"
					f"  Tug‘ilgan sana: {emp.date_of_birth}\n"
					f"  Manzil: {emp.address}\n"
					f"  Email: {emp.email}\n"
					f"  Lavozim va fan: {emp.position}\n"
					f"  Ish boshlagan sana: {emp.start_date}\n\n"
				)

		if students:
			response_text += "Tarbiyalanuvchilar / Воспитанники:\n"
			for stu in students:
				response_text += (
					f"- Ism: {stu.full_name}\n"
					f"  Muassasa turi: Markaz\n"
					f"  Tug‘ilgan sana: {stu.date_of_birth}\n"
					f"  Yoshi: {stu.age}\n"
					f"  Manzil: {stu.address}\n"
					f"  Diagnoz: {stu.diagnosis}\n"
					f"  Qatnashish kunlari: {stu.attendance_days}\n"
					f"  Ota-ona/vasiy: {stu.parent_name}\n"
					f"  Ota-ona email: {stu.parent_email}\n"
					f"  Ota-ona telefoni: {stu.parent_phone}\n\n"
				)

		keyboard = InlineKeyboardMarkup(inline_keyboard=[
			[InlineKeyboardButton(text="Orqaga / Назад", callback_data="show_responses")]
		])
		await callback.message.edit_text(response_text, reply_markup=keyboard)
		await callback.answer()


@dp.message(SurveyTypeForm.language)
async def process_language(message: Message, state: FSMContext):
	if message.from_user.id == ADMIN_ID:
		logger.warning(f"Admin {message.from_user.id} attempted to select language")
		await message.answer(
			"Siz admin sifatida faqat javoblarni ko‘rishingiz mumkin / Вы, как администратор, можете только просматривать ответы."
		)
		return

	language = message.text
	logger.info(f"User {message.from_user.id} selected language: {language}")
	if language == "🇺🇿 O‘zbekcha":
		await state.update_data(language=Language.UZBEK, lang_text="uz")
		await message.answer("Telefon raqamingizni ulashish uchun tugmani bosing:",
							 reply_markup=get_contact_keyboard("uz"))
	elif language == "🇷🇺 Русский":
		await state.update_data(language=Language.RUSSIAN, lang_text="ru")
		await message.answer("Нажмите кнопку, чтобы поделиться номером телефона:",
							 reply_markup=get_contact_keyboard("ru"))
	else:
		logger.warning(f"User {message.from_user.id} sent invalid language: {language}")
		await message.answer("Iltimos, faqat berilgan tilni tanlang / Пожалуйста, выберите только предложенный язык.")
		return
	await state.set_state(SurveyTypeForm.user_phone)


@dp.message(SurveyTypeForm.user_phone, F.contact)
async def process_user_phone(message: Message, state: FSMContext):
	if message.from_user.id == ADMIN_ID:
		logger.warning(f"Admin {message.from_user.id} attempted to submit phone number")
		await message.answer(
			"Siz admin sifatida faqat javoblarni ko‘rishingiz mumkin / Вы, как администратор, можете только просматривать ответы."
		)
		return

	if not message.contact or not message.contact.phone_number:
		data = await state.get_data()
		lang = data.get("lang_text", "uz")
		logger.warning(f"User {message.from_user.id} sent empty contact")
		await message.answer(
			"Iltimos, telefon raqamingizni ulashing." if lang == "uz" else "Пожалуйста, поделитесь номером телефона.",
			reply_markup=get_contact_keyboard(lang)
		)
		return
	phone = message.contact.phone_number
	if not re.match(PHONE_REGEX, phone):
		data = await state.get_data()
		lang = data.get("lang_text", "uz")
		logger.warning(f"User {message.from_user.id} sent invalid phone format: {phone}")
		await message.answer(
			"Telefon raqami noto‘g‘ri formatda (10-15 raqam kerak). Iltimos, qayta urining." if lang == "uz" else
			"Номер телефона в неверном формате (нужно 10-15 цифр). Пожалуйста, попробуйте снова.",
			reply_markup=get_contact_keyboard(lang)
		)
		return
	logger.info(f"User {message.from_user.id} shared phone: {phone}")
	await state.update_data(user_phone=phone)
	data = await state.get_data()
	lang = data.get("lang_text", "uz")
	await message.answer(
		"Siz qaysi muassasadan kelyapsiz? / Из какого учреждения вы?:" if lang == "uz" else
		"Из какого учреждения вы? / Siz qaysi muassasadan kelyapsiz?:",
		reply_markup=get_institution_type_keyboard()
	)
	await state.set_state(SurveyTypeForm.institution_type)


@dp.message(SurveyTypeForm.institution_type)
async def process_institution_type(message: Message, state: FSMContext):
	if message.from_user.id == ADMIN_ID:
		logger.warning(f"Admin {message.from_user.id} attempted to select institution type")
		await message.answer(
			"Siz admin sifatida faqat javoblarni ko‘rish mumkin / Вы, как администратор, можете только просматривать ответы."
		)
		return

	institution_type = message.text
	data = await state.get_data()
	lang = data.get("lang_text", "uz")
	logger.info(f"User {message.from_user.id} selected institution type: {institution_type}")

	if institution_type == "Bog‘cha, Maktab / Детский сад, Школа":
		await state.update_data(institution_type=InstitutionType.BOGCHA_MAKTAB.value)
		await message.answer(
			"Kim uchun ma'lumot kiritmoqdasiz?:" if lang == "uz" else "Для кого вы вводите данные?:",
			reply_markup=get_survey_type_keyboard()
		)
		await state.set_state(SurveyTypeForm.survey_type)
	elif institution_type == "Markaz / Центр":
		await state.update_data(institution_type=InstitutionType.MARKAZ.value)
		await message.answer(
			"Kim uchun ma'lumot kiritmoqdasiz?:" if lang == "uz" else "Для кого вы вводите данные?:",
			reply_markup=get_survey_type_keyboard()
		)
		await state.set_state(SurveyTypeForm.survey_type)
	else:
		logger.warning(f"User {message.from_user.id} sent invalid institution type: {institution_type}")
		await message.answer(
			"Iltimos, faqat berilgan variantni tanlang (Bog‘cha, Maktab yoki Markaz)." if lang == "uz" else
			"Пожалуйста, выберите только предложенный вариант (Bog‘cha, Maktab или Markaz)."
		)


@dp.message(SurveyTypeForm.user_phone)
async def process_user_phone_fallback(message: Message, state: FSMContext):
	if message.from_user.id == ADMIN_ID:
		logger.warning(f"Admin {message.from_user.id} attempted to submit phone number")
		await message.answer(
			"Siz admin sifatida faqat javoblarni ko‘rishingiz mumkin / Вы, как администратор, можете только просматривать ответы."
		)
		return

	data = await state.get_data()
	lang = data.get("lang_text", "uz")
	logger.warning(f"User {message.from_user.id} sent text instead of contact: {message.text}")
	await message.answer(
		"Iltimos, telefon raqamingizni ulashish uchun tugmani bosing." if lang == "uz" else
		"Пожалуйста, нажмите кнопку, чтобы поделиться номером телефона.",
		reply_markup=get_contact_keyboard(lang)
	)


@dp.message(SurveyTypeForm.survey_type)
async def process_survey_type(message: Message, state: FSMContext):
	if message.from_user.id == ADMIN_ID:
		logger.warning(f"Admin {message.from_user.id} attempted to select survey type")
		await message.answer(
			"Siz admin sifatida faqat javoblarni ko‘rishingiz mumkin / Вы, как администратор, можете только просматривать ответы."
		)
		return

	survey_type = message.text
	data = await state.get_data()
	lang = data.get("lang_text", "uz")
	logger.info(f"User {message.from_user.id} selected survey type: {survey_type}")
	if survey_type == "Xodim (O‘qituvchi) / Сотрудник (Преподаватель)":
		await message.answer(
			"To‘liq ism, familiyangiz?:" if lang == "uz" else "Введите ваше полное имя:"
		)
		await state.set_state(EmployeeForm.full_name)
	elif survey_type == "Tarbiyalanuvchi / Воспитанник":
		await message.answer(
			"Bola ismi va familiyasi?:" if lang == "uz" else "Имя и фамилия ребёнка?:"
		)
		await state.set_state(StudentForm.full_name)
	else:
		logger.warning(f"User {message.from_user.id} sent invalid survey type: {survey_type}")
		await message.answer(
			"Iltimos, faqat berilgan variantni tanlang." if lang == "uz" else
			"Пожалуйста, выберите только предложенный вариант."
		)
		return


@dp.message(EmployeeForm.full_name)
async def process_employee_full_name(message: Message, state: FSMContext):
	if message.from_user.id == ADMIN_ID:
		logger.warning(f"Admin {message.from_user.id} attempted to submit employee full name")
		await message.answer(
			"Siz admin sifatida faqat javoblarni ko‘rishingiz mumkin / Вы, как администратор, можете только просматривать ответы."
		)
		return

	if not message.text.strip():
		data = await state.get_data()
		lang = data.get("lang_text", "uz")
		logger.warning(f"User {message.from_user.id} sent empty full_name")
		await message.answer(
			"Iltimos, to‘liq ismni kiriting." if lang == "uz" else "Пожалуйста, введите полное имя."
		)
		return
	logger.info(f"User {message.from_user.id} entered full_name: {message.text}")
	await state.update_data(full_name=message.text)
	data = await state.get_data()
	lang = data.get("lang_text", "uz")
	await message.answer(
		"Tug‘ilgan sanangiz? (YYYY-MM-DD):" if lang == "uz" else "Дата рождения? (ГГГГ-ММ-ДД):"
	)
	await state.set_state(EmployeeForm.date_of_birth)


@dp.message(EmployeeForm.date_of_birth)
async def process_employee_date_of_birth(message: Message, state: FSMContext):
	if message.from_user.id == ADMIN_ID:
		logger.warning(f"Admin {message.from_user.id} attempted to submit employee date of birth")
		await message.answer(
			"Siz admin sifatida faqat javoblarni ko‘rishingiz mumkin / Вы, как администратор, можете только просматривать ответы."
		)
		return

	try:
		datetime.strptime(message.text, "%Y-%m-%d")
		logger.info(f"User {message.from_user.id} entered date_of_birth: {message.text}")
		await state.update_data(date_of_birth=message.text)
	except ValueError:
		data = await state.get_data()
		lang = data.get("lang_text", "uz")
		logger.warning(f"User {message.from_user.id} sent invalid date_of_birth: {message.text}")
		await message.answer(
			"Iltimos, sanani to‘g‘ri formatda kiriting (YYYY-MM-DD)." if lang == "uz" else
			"Пожалуйста, введите дату в правильном формате (ГГГГ-ММ-ДД)."
		)
		return
	data = await state.get_data()
	lang = data.get("lang_text", "uz")
	await message.answer(
		"Yashash manzilingiz?:" if lang == "uz" else "Адрес проживания?:"
	)
	await state.set_state(EmployeeForm.address)


@dp.message(EmployeeForm.address)
async def process_employee_address(message: Message, state: FSMContext):
	if message.from_user.id == ADMIN_ID:
		logger.warning(f"Admin {message.from_user.id} attempted to submit employee address")
		await message.answer(
			"Siz admin sifatida faqat javoblarni ko‘rishingiz mumkin / Вы, как администратор, можете только просматривать ответы."
		)
		return

	if not message.text.strip():
		data = await state.get_data()
		lang = data.get("lang_text", "uz")
		logger.warning(f"User {message.from_user.id} sent empty address")
		await message.answer(
			"Iltimos, manzilni kiriting." if lang == "uz" else "Пожалуйста, введите адрес."
		)
		return
	logger.info(f"User {message.from_user.id} entered address: {message.text}")
	await state.update_data(address=message.text)
	data = await state.get_data()
	lang = data.get("lang_text", "uz")
	await message.answer(
		"Elektron pochtangiz?:" if lang == "uz" else "Электронная почта?:"
	)
	await state.set_state(EmployeeForm.email)


@dp.message(EmployeeForm.email)
async def process_employee_email(message: Message, state: FSMContext):
	if message.from_user.id == ADMIN_ID:
		logger.warning(f"Admin {message.from_user.id} attempted to submit employee email")
		await message.answer(
			"Siz admin sifatida faqat javoblarni ko‘rishingiz mumkin / Вы, как администратор, можете только просматривать ответы."
		)
		return

	if not re.match(EMAIL_REGEX, message.text):
		data = await state.get_data()
		lang = data.get("lang_text", "uz")
		logger.warning(f"User {message.from_user.id} sent invalid email: {message.text}")
		await message.answer(
			"Iltimos, to‘g‘ri elektron pochta kiriting (masalan, example@domain.com)." if lang == "uz" else
			"Пожалуйста, введите корректный адрес электронной почты (например, example@domain.com)."
		)
		return
	logger.info(f"User {message.from_user.id} entered email: {message.text}")
	await state.update_data(email=message.text)
	data = await state.get_data()
	lang = data.get("lang_text", "uz")
	await message.answer(
		"Lavozimingiz va fan (agar o‘qituvchi bo‘lsangiz)?:" if lang == "uz" else
		"Ваша должность и предмет (если вы преподаватель)?:"
	)
	await state.set_state(EmployeeForm.position)


@dp.message(EmployeeForm.position)
async def process_employee_position(message: Message, state: FSMContext):
	if message.from_user.id == ADMIN_ID:
		logger.warning(f"Admin {message.from_user.id} attempted to submit employee position")
		await message.answer(
			"Siz admin sifatida faqat javoblarni ko‘rishingiz mumkin / Вы, как администратор, можете только просматривать ответы."
		)
		return

	if not message.text.strip():
		data = await state.get_data()
		lang = data.get("lang_text", "uz")
		logger.warning(f"User {message.from_user.id} sent empty position")
		await message.answer(
			"Iltimos, lavozimni kiriting." if lang == "uz" else "Пожалуйста, введите должность."
		)
		return
	logger.info(f"User {message.from_user.id} entered position: {message.text}")
	await state.update_data(position=message.text)
	data = await state.get_data()
	lang = data.get("lang_text", "uz")
	await message.answer(
		"Ish boshlagan sanangiz? (YYYY-MM-DD):" if lang == "uz" else "Дата начала работы? (ГГГГ-ММ-ДД):"
	)
	await state.set_state(EmployeeForm.start_date)


@dp.message(EmployeeForm.start_date)
async def process_employee_start_date(message: Message, state: FSMContext):
	if message.from_user.id == ADMIN_ID:
		logger.warning(f"Admin {message.from_user.id} attempted to submit employee start date")
		await message.answer(
			"Siz admin sifatida faqat javoblarni ko‘rishingiz mumkin / Вы, как администратор, можете только просматривать ответы."
		)
		return

	try:
		datetime.strptime(message.text, "%Y-%m-%d")
		logger.info(f"User {message.from_user.id} entered start_date: {message.text}")
	except ValueError:
		data = await state.get_data()
		lang = data.get("lang_text", "uz")
		logger.warning(f"User {message.from_user.id} sent invalid start_date: {message.text}")
		await message.answer(
			"Iltimos, sanani to‘g‘ri formatda kiriting (YYYY-MM-DD)." if lang == "uz" else
			"Пожалуйста, введите дату в правильном формате (ГГГГ-ММ-ДД)."
		)
		return

	data = await state.get_data()
	lang = data.get("lang_text", "uz")

	try:
		with SessionLocal() as session:
			employee = Employee(
				full_name=data["full_name"],
				date_of_birth=datetime.strptime(data["date_of_birth"], "%Y-%m-%d").date(),
				address=data["address"],
				email=data["email"],
				position=data["position"],
				subject=data["position"] if "o‘qituvchi" in data["position"].lower() or "преподаватель" in data[
					"position"].lower() else None,
				start_date=datetime.strptime(message.text, "%Y-%m-%d").date(),
				language=data["language"],
				user_phone=data["user_phone"],
				institution_type=InstitutionType(data["institution_type"])
			)
			print(employee)
			session.add(employee)
			session.commit()
		logger.info(
			f"User {message.from_user.id} saved employee: {data['full_name']}, user_phone: {data['user_phone']}, "
			f"{InstitutionType(data['institution_type'])}")
	except Exception as e:
		logger.error(f"User {message.from_user.id} failed to save employee: {str(e)}")
		await message.answer(
			"Ma'lumotlarni saqlashda xato yuz berdi. Iltimos, qayta urining." if lang == "uz" else
			"Произошла ошибка при сохранении данных. Пожалуйста, попробуйте снова."
		)
		return

	await message.answer(
		"OK, rahmat" if lang == "uz" else "OK, спасибо"
	)
	await state.clear()


@dp.message(StudentForm.full_name)
async def process_student_full_name(message: Message, state: FSMContext):
	if message.from_user.id == ADMIN_ID:
		logger.warning(f"Admin {message.from_user.id} attempted to submit student full name")
		await message.answer(
			"Siz admin sifatida faqat javoblarni ko‘rishingiz mumkin / Вы, как администратор, можете только просматривать ответы."
		)
		return

	if not message.text.strip():
		data = await state.get_data()
		lang = data.get("lang_text", "uz")
		logger.warning(f"User {message.from_user.id} sent empty student full_name")
		await message.answer(
			"Iltimos, bola ismi va familiyasini kiriting." if lang == "uz" else
			"Пожалуйста, введите имя и фамилию ребёнка."
		)
		return
	logger.info(f"User {message.from_user.id} entered student full_name: {message.text}")
	await state.update_data(full_name=message.text)
	data = await state.get_data()
	lang = data.get("lang_text", "uz")
	await message.answer(
		"Tug‘ilgan sanasi? (YYYY-MM-DD):" if lang == "uz" else "Дата рождения? (ГГГГ-ММ-ДД):"
	)
	await state.set_state(StudentForm.date_of_birth)


@dp.message(StudentForm.date_of_birth)
async def process_student_date_of_birth(message: Message, state: FSMContext):
	if message.from_user.id == ADMIN_ID:
		logger.warning(f"Admin {message.from_user.id} attempted to submit student date of birth")
		await message.answer(
			"Siz admin sifatida faqat javoblarni ko‘rishingiz mumkin / Вы, как администратор, можете только просматривать ответы."
		)
		return

	try:
		datetime.strptime(message.text, "%Y-%m-%d")
		logger.info(f"User {message.from_user.id} entered student date_of_birth: {message.text}")
		await state.update_data(date_of_birth=message.text)
	except ValueError:
		data = await state.get_data()
		lang = data.get("lang_text", "uz")
		logger.warning(f"User {message.from_user.id} sent invalid student date_of_birth: {message.text}")
		await message.answer(
			"Iltimos, sanani to‘g‘ri formatda kiriting (YYYY-MM-DD)." if lang == "uz" else
			"Пожалуйста, введите дату в правильном формате (ГГГГ-ММ-ДД)."
		)
		return
	data = await state.get_data()
	lang = data.get("lang_text", "uz")
	await message.answer(
		"Yoshi?:" if lang == "uz" else "Возраст?:"
	)
	await state.set_state(StudentForm.age)


@dp.message(StudentForm.age)
async def process_student_age(message: Message, state: FSMContext):
	if message.from_user.id == ADMIN_ID:
		logger.warning(f"Admin {message.from_user.id} attempted to submit student age")
		await message.answer(
			"Siz admin sifatida faqat javoblarni ko‘rishingiz mumkin / Вы, как администратор, можете только просматривать ответы."
		)
		return

	try:
		age = int(message.text)
		if age <= 0:
			raise ValueError
		logger.info(f"User {message.from_user.id} entered student age: {age}")
		await state.update_data(age=age)
	except ValueError:
		data = await state.get_data()
		lang = data.get("lang_text", "uz")
		logger.warning(f"User {message.from_user.id} sent invalid student age: {message.text}")
		await message.answer(
			"Iltimos, yoshni to‘g‘ri raqamda kiriting." if lang == "uz" else
			"Пожалуйста, введите возраст корректным числом."
		)
		return
	data = await state.get_data()
	lang = data.get("lang_text", "uz")
	await message.answer(
		"Yashash manzili?:" if lang == "uz" else "Адрес проживания?:"
	)
	await state.set_state(StudentForm.address)


@dp.message(StudentForm.address)
async def process_student_address(message: Message, state: FSMContext):
	if message.from_user.id == ADMIN_ID:
		logger.warning(f"Admin {message.from_user.id} attempted to submit student address")
		await message.answer(
			"Siz admin sifatida faqat javoblarni ko‘rishingiz mumkin / Вы, как администратор, можете только просматривать ответы."
		)
		return

	if not message.text.strip():
		data = await state.get_data()
		lang = data.get("lang_text", "uz")
		logger.warning(f"User {message.from_user.id} sent empty student address")
		await message.answer(
			"Iltimos, manzilni kiriting." if lang == "uz" else "Пожалуйста, введите адрес."
		)
		return
	logger.info(f"User {message.from_user.id} entered student address: {message.text}")
	await state.update_data(address=message.text)
	data = await state.get_data()
	lang = data.get("lang_text", "uz")
	await message.answer(
		"Diagnozi qanday?:" if lang == "uz" else "Какой диагноз у ребёнка?:"
	)
	await state.set_state(StudentForm.diagnosis)


@dp.message(StudentForm.diagnosis)
async def process_student_diagnosis(message: Message, state: FSMContext):
	if message.from_user.id == ADMIN_ID:
		logger.warning(f"Admin {message.from_user.id} attempted to submit student diagnosis")
		await message.answer(
			"Siz admin sifatida faqat javoblarni ko‘rishingiz mumkin / Вы, как администратор, можете только просматривать ответы."
		)
		return

	if not message.text.strip():
		data = await state.get_data()
		lang = data.get("lang_text", "uz")
		logger.warning(f"User {message.from_user.id} sent empty student diagnosis")
		await message.answer(
			"Iltimos, diagnozni kiriting." if lang == "uz" else "Пожалуйста, введите диагноз."
		)
		return
	logger.info(f"User {message.from_user.id} entered student diagnosis: {message.text}")
	await state.update_data(diagnosis=message.text)
	data = await state.get_data()
	lang = data.get("lang_text", "uz")
	await message.answer(
		"Haftaning qaysi kunlari qatnashadi?:" if lang == "uz" else "В какие дни посещает?:"
	)
	await state.set_state(StudentForm.attendance_days)


@dp.message(StudentForm.attendance_days)
async def process_student_attendance_days(message: Message, state: FSMContext):
	if message.from_user.id == ADMIN_ID:
		logger.warning(f"Admin {message.from_user.id} attempted to submit student attendance days")
		await message.answer(
			"Siz admin sifatida faqat javoblarni ko‘rishingiz mumkin / Вы, как администратор, можете только просматривать ответы."
		)
		return

	if not message.text.strip():
		data = await state.get_data()
		lang = data.get("lang_text", "uz")
		logger.warning(f"User {message.from_user.id} sent empty student attendance_days")
		await message.answer(
			"Iltimos, qatnashadigan kunlarni kiriting." if lang == "uz" else
			"Пожалуйста, введите дни посещения."
		)
		return
	logger.info(f"User {message.from_user.id} entered student attendance_days: {message.text}")
	await state.update_data(attendance_days=message.text)
	data = await state.get_data()
	lang = data.get("lang_text", "uz")
	await message.answer(
		"Ota-ona yoki vasiy ismi?:" if lang == "uz" else "Имя родителя или опекуна?:"
	)
	await state.set_state(StudentForm.parent_name)


@dp.message(StudentForm.parent_name)
async def process_student_parent_name(message: Message, state: FSMContext):
	if message.from_user.id == ADMIN_ID:
		logger.warning(f"Admin {message.from_user.id} attempted to submit student parent name")
		await message.answer(
			"Siz admin sifatida faqat javoblarni ko‘rishingiz mumkin / Вы, как администратор, можете только просматривать ответы."
		)
		return

	if not message.text.strip():
		data = await state.get_data()
		lang = data.get("lang_text", "uz")
		logger.warning(f"User {message.from_user.id} sent empty student parent_name")
		await message.answer(
			"Iltimos, ota-ona yoki vasiy ismini kiriting." if lang == "uz" else
			"Пожалуйста, введите имя родителя или опекуна."
		)
		return
	logger.info(f"User {message.from_user.id} entered student parent_name: {message.text}")
	await state.update_data(parent_name=message.text)
	data = await state.get_data()
	lang = data.get("lang_text", "uz")
	await message.answer(
		"Elektron pochta?:" if lang == "uz" else "Электронная почта?:"
	)
	await state.set_state(StudentForm.parent_email)


@dp.message(StudentForm.parent_email)
async def process_student_parent_email(message: Message, state: FSMContext):
	if message.from_user.id == ADMIN_ID:
		logger.warning(f"Admin {message.from_user.id} attempted to submit student parent email")
		await message.answer(
			"Siz admin sifatida faqat javoblarni ko‘rishingiz mumkin / Вы, как администратор, можете только просматривать ответы."
		)
		return

	if not re.match(EMAIL_REGEX, message.text):
		data = await state.get_data()
		lang = data.get("lang_text", "uz")
		logger.warning(f"User {message.from_user.id} sent invalid student parent_email: {message.text}")
		await message.answer(
			"Iltimos, to‘g‘ri elektron pochta kiriting (masalan, example@domain.com)." if lang == "uz" else
			"Пожалуйста, введите корректный адрес электронной почты (например, example@domain.com)."
		)
		return
	logger.info(f"User {message.from_user.id} entered student parent_email: {message.text}")
	await state.update_data(parent_email=message.text)
	data = await state.get_data()
	lang = data.get("lang_text", "uz")
	await message.answer(
		"Telefon raqami?:" if lang == "uz" else "Контактный номер телефона?:"
	)
	await state.set_state(StudentForm.parent_phone)


@dp.message(StudentForm.parent_phone)
async def process_student_parent_phone(message: Message, state: FSMContext):
	if message.from_user.id == ADMIN_ID:
		logger.warning(f"Admin {message.from_user.id} attempted to submit student parent phone")
		await message.answer(
			"Siz admin sifatida faqat javoblarni ko‘rishingiz mumkin / Вы, как администратор, можете только просматривать ответы."
		)
		return

	if not re.match(PHONE_REGEX, message.text):
		data = await state.get_data()
		lang = data.get("lang_text", "uz")
		logger.warning(f"User {message.from_user.id} sent invalid student parent_phone: {message.text}")
		await message.answer(
			"Iltimos, to‘g‘ri telefon raqamini kiriting (10-15 raqam, + bilan yoki bilansiz)." if lang == "uz" else
			"Пожалуйста, введите корректный номер телефона (10-15 цифр, с + или без)."
		)
		return
	logger.info(f"User {message.from_user.id} entered student parent_phone: {message.text}")
	await state.update_data(parent_phone=message.text)
	data = await state.get_data()
	lang = data.get("lang_text", "uz")

	try:
		with SessionLocal() as session:
			student = Student(
				full_name=data["full_name"],
				date_of_birth=datetime.strptime(data["date_of_birth"], "%Y-%m-%d").date(),
				age=int(data["age"]),
				address=data["address"],
				diagnosis=data["diagnosis"],
				attendance_days=data["attendance_days"],
				parent_name=data["parent_name"],
				parent_email=data["parent_email"],
				parent_phone=message.text,
				language=data["language"],
				user_phone=data["user_phone"],
				institution_type=InstitutionType(data["institution_type"])

			)
			session.add(student)
			session.commit()
		logger.info(f"User {message.from_user.id} saved student: {data['full_name']}, user_phone: {data['user_phone']}")
	except Exception as e:
		logger.error(f"User {message.from_user.id} failed to save student: {str(e)}")
		await message.answer(
			"Ma'lumotlarni saqlashda xato yuz berdi. Iltimos, qayta urining." if lang == "uz" else
			"Произошла ошибка при сохранении данных. Пожалуйста, попробуйте снова."
		)
		return

	await message.answer(
		"OK, rahmat" if lang == "uz" else "OK, спасибо"
	)
	await state.clear()


async def main():
	await dp.start_polling(bot)


if __name__ == "__main__":
	asyncio.run(main())
