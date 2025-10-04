import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Inline головне меню
main_menu = InlineKeyboardMarkup(row_width=1)
main_menu.add(
    InlineKeyboardButton("Запис на тренування", callback_data="start_form"),
    InlineKeyboardButton("Прайс / Інформація", callback_data="show_price")
)

# Inline меню графіку
schedule_menu = InlineKeyboardMarkup(row_width=1)
schedule_menu.add(
    InlineKeyboardButton("1: Пн / Ср / Пт", callback_data="schedule_1"),
    InlineKeyboardButton("2: Вт / Чт / Сб", callback_data="schedule_2"),
    InlineKeyboardButton("3: Пн / Вт / Чт / Пт", callback_data="schedule_3"),
    InlineKeyboardButton("Скасувати", callback_data="cancel")
)

# Inline меню прайсу
price_menu = InlineKeyboardMarkup(row_width=1)
price_menu.add(
    InlineKeyboardButton("Промо тренування", callback_data="promo"),
    InlineKeyboardButton("Пакет 12 / 16 тренувань", callback_data="package"),
    InlineKeyboardButton("Назад", callback_data="back_to_main")
)

# Inline кнопка Скасувати
form_keyboard = InlineKeyboardMarkup(row_width=1)
form_keyboard.add(InlineKeyboardButton("Скасувати", callback_data="cancel"))

# Стан машини для запису
class Form(StatesGroup):
    age = State()
    gender = State()
    health = State()
    weight = State()
    experience = State()
    goal = State()
    schedule = State()
    contact = State()

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Привіт! Обери дію:", reply_markup=main_menu)

@dp.message_handler(commands=['get_id'])
async def get_id(message: types.Message):
    await message.answer(f"Ваш chat_id: {message.chat.id}")

@dp.callback_query_handler(lambda c: c.data == "start_form")
async def start_form(callback: types.CallbackQuery):
    await Form.age.set()
    await bot.send_message(callback.from_user.id, "Вік:", reply_markup=form_keyboard)

@dp.callback_query_handler(lambda c: c.data == "cancel", state="*")
async def cancel_step(callback: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    data = await state.get_data()

    previous_states = [
        Form.age.state,
        Form.gender.state,
        Form.health.state,
        Form.weight.state,
        Form.experience.state,
        Form.goal.state,
        Form.schedule.state,
        Form.contact.state
    ]

    questions = {
        Form.age.state: "Вік:",
        Form.gender.state: "Стать:",
        Form.health.state: "Хронічні захворювання / травми / операції:",
        Form.weight.state: "Вага:",
        Form.experience.state: "Досвід / стаж тренувань:",
        Form.goal.state: "Фокус / ціль:",
        Form.schedule.state: "Оберіть графік:",
        Form.contact.state: "Контакти: tg / insta / viber:"
    }

    if current_state in previous_states:
        index = previous_states.index(current_state)
        if index > 0:
            previous_state = previous_states[index - 1]
            await state.set_state(previous_state)
            question_text = questions.get(previous_state, "Введіть нову відповідь:")

            # Визначення відповідної клавіатури
            if previous_state == Form.schedule.state:
                keyboard = schedule_menu
            else:
                keyboard = form_keyboard

            await bot.send_message(
                callback.from_user.id,
                f"⬅️ Повертаємось назад.\n{question_text}",
reply_markup=keyboard
            )
        else:
            await state.finish()
            await bot.send_message(callback.from_user.id, "Скасовано. Повертаю в головне меню:", reply_markup=main_menu)
    else:
        await bot.send_message(callback.from_user.id, "Неможливо скасувати цей етап.")

@dp.message_handler(content_types=['text'], state=Form.age)
async def process_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await Form.gender.set()
    await message.answer("Стать:", reply_markup=form_keyboard)

@dp.message_handler(content_types=['text'], state=Form.gender)
async def process_gender(message: types.Message, state: FSMContext):
    await state.update_data(gender=message.text)
    await Form.health.set()
    await message.answer("Хронічні захворювання / травми / операції:", reply_markup=form_keyboard)

@dp.message_handler(content_types=['text'], state=Form.health)
async def process_health(message: types.Message, state: FSMContext):
    await state.update_data(health=message.text)
    await Form.weight.set()
    await message.answer("Вага:", reply_markup=form_keyboard)

@dp.message_handler(content_types=['text'], state=Form.weight)
async def process_weight(message: types.Message, state: FSMContext):
    await state.update_data(weight=message.text)
    await Form.experience.set()
    await message.answer("Досвід / стаж тренувань:", reply_markup=form_keyboard)

@dp.message_handler(content_types=['text'], state=Form.experience)
async def process_experience(message: types.Message, state: FSMContext):
    await state.update_data(experience=message.text)
    await Form.goal.set()
    await message.answer("Фокус / ціль:", reply_markup=form_keyboard)

@dp.message_handler(content_types=['text'], state=Form.goal)
async def process_goal(message: types.Message, state: FSMContext):
    await state.update_data(goal=message.text)
    await Form.schedule.set()
    await message.answer("Оберіть графік:", reply_markup=schedule_menu)

@dp.callback_query_handler(lambda c: c.data.startswith("schedule_"), state=Form.schedule)
async def process_schedule(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(schedule=callback.data.replace("schedule_", ""))
    await Form.contact.set()
    await bot.send_message(callback.from_user.id, "Контакти: tg / insta / viber:", reply_markup=form_keyboard)

@dp.message_handler(content_types=['text'], state=Form.contact)
async def process_contact(message: types.Message, state: FSMContext):
    data = await state.get_data()

    summary = (
        f"📥 Нова заявка на тренування:\n\n"
        f"👤 Вік: {data['age']}\n"
        f"👤 Стать: {data['gender']}\n"
        f"⚕️ Хронічні захворювання / травми / операції: {data['health']}\n"
        f"⚖️ Вага: {data['weight']}\n"
        f"🏋️‍♂️ Досвід / стаж тренувань: {data['experience']}\n"
        f"🎯 Ціль: {data['goal']}\n"
        f"📅 Графік: {data['schedule']}\n"
        f"📱 Контакти: {message.text}"
    )

    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=summary)
    await message.answer("Запис створено.\nНезабаром з вами зв'яжеться тренер.", reply_markup=main_menu)
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == "show_price")
async def show_price_menu(callback: types.CallbackQuery):
    await bot.send_message(callback.from_user.id, "Оберіть:", reply_markup=price_menu)

@dp.callback_query_handler(lambda c: c.data == "promo")
async def promo_info(callback: types.CallbackQuery):
    await bot.send_message(
        callback.from_user.id,
        "Безкоштовне / ознайомче тренування по типу фул баді тривалістю +/- 1,5 години.\n"
        "Акценти виділятиму по ходу за твоїм бажанням.\n"
        "Вільний формат.\n"
        "Візьми з собою 1,5л води.\n"
        "Прийом їжі за 2 години до початку."
    )
@dp.callback_query_handler(lambda c: c.data == "package")
async def package_info(callback: types.CallbackQuery):
    await bot.send_message(
        callback.from_user.id,
        "Вартість: 4500 / 5600 грн. Парне -50%.\n"
        "+ Розрахунок КБЖВ під твої данні, ціль, активність.\n"
        "+ Консультації по нутриціології.\n"
        "+ Ведення особистого щоденника тренувань."
    )
@dp.callback_query_handler(lambda c: c.data == "package")
async def package_info(callback: types.CallbackQuery):
    await bot.send_message(
        callback.from_user.id,
        "Вартість: 4500 / 5600 грн. Парне -50%.\n"
        "+ Розрахунок КБЖВ під твої данні, ціль, активність.\n"
        "+ Консультації по нутриціології.\n"
        "+ Ведення особистого щоденника тренувань."
    )

@dp.callback_query_handler(lambda c: c.data == "back_to_main")
async def go_back(callback: types.CallbackQuery):
    await bot.send_message(callback.from_user.id, "Повертаю в головне меню:", reply_markup=main_menu)

if __name__ == '__main__':


from aiohttp import web
from aiogram.utils.executor import start_webhook

WEBHOOK_HOST = "https://ИМЯ-ПРОЕКТА.deta.space"  # замени после деплоя
WEBHOOK_PATH = "/"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8000))  # Deta использует порт 8000

async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(dp):
    await bot.delete_webhook()

if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )




