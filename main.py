from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

API_TOKEN = '7261530454:AAFyfYScsoMSdHyQ2N8nf4oQ0MUMW7GXfAc'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(
            text="Открыть мини-приложение 🍕",
            web_app=types.WebAppInfo(url="https://python-project3-brown.vercel.app/")
        )
    )
    await message.answer("Привет! Жми кнопку и регистрируйся:", reply_markup=keyboard)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

