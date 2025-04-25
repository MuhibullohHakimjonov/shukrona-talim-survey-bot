from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def get_language_keyboard():
	keyboard = [
		[
			KeyboardButton(text="🇺🇿 O‘zbekcha"),
			KeyboardButton(text="🇷🇺 Русский")
		]
	]
	return ReplyKeyboardMarkup(
		keyboard=keyboard,
		resize_keyboard=True,
		one_time_keyboard=True
	)


def get_survey_type_keyboard():
	keyboard = [
		[KeyboardButton(text="Xodim (O‘qituvchi) / Сотрудник (Преподаватель)")],
		[KeyboardButton(text="Tarbiyalanuvchi / Воспитанник")]
	]
	return ReplyKeyboardMarkup(
		keyboard=keyboard,
		resize_keyboard=True,
		one_time_keyboard=True
	)


def get_institution_type_keyboard():
	keyboard = [
		[KeyboardButton(text="Bog‘cha, Maktab / Детский сад, Школа")],
		[KeyboardButton(text="Markaz / Центр")]
	]
	return ReplyKeyboardMarkup(
		keyboard=keyboard,
		resize_keyboard=True,
		one_time_keyboard=True
	)


def get_contact_keyboard(lang: str):
	if lang == "uz":
		text = "Telefon raqamni ulashish"
	else:
		text = "Поделиться номером телефона"
	keyboard = [
		[KeyboardButton(text=text, request_contact=True)]
	]
	return ReplyKeyboardMarkup(
		keyboard=keyboard,
		resize_keyboard=True,
		one_time_keyboard=True
	)
