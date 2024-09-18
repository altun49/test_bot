from aiogram import Bot, Dispatcher
from aiogram.filters import BaseFilter
from aiogram.types import Message
from environs import Env

env = Env()
env.read_env()

bot_token = env('BOT_TOKEN')
admin_id = env.int('ADMIN_ID')

bot = Bot(bot_token)
dp = Dispatcher()


class IsAdmin(BaseFilter):
    def __init__(self, admin_ids: list[int]) -> None:
        self.admin_ids = admin_ids

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in self.admin_ids


@dp.message(IsAdmin(admin_id))
async def answer_if_admins_update(message: Message):
    await message.answer(text='Вы админ')


@dp.message()
async def answer_if_not_admins_update(message: Message):
    await message.answer(text='Вы не админ')


if __name__ == '__main__':
    dp.run_polling(bot)
