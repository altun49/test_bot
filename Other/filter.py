# тренировка написания фильтров для хендлеров
# напишу фильтр, который будет принимать апдейт с типом фото и
# текст который начинается со слов ["привет", "мд"] не завися от регистра
# хендлер должен возвращать сообщение "привет" или "д" на сообщение, а если фото "вай как красиво!" иначе скип
from Bot.main import *


@dp.message(F.photo | F.text.lower().in_(['привет', 'мд']))
async def typical_message_for_anon_chat_tg(message: Message) -> bool:
    if message.photo:
        await message.answer(
            "вай как красиво!"
        )
    elif message.text.lower() in (['привет']):
        await message.answer(
            "привет"
        )
    elif message.text.lower() in (['мд']):
        await message.answer(
            "д"
        )
    else:
        await message.answer(
            "скип"
        )

