# TG_TOKEN = os.getenv('8212268365:AAHB5JcBUxK_HrsykkMbtE4cFHOiNu34uWA', 0)

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from app.handlers_analyzer import router as analyzer_router

import logging
import os
import asyncio

logging.basicConfig(level=logging.INFO)

load_dotenv()
TG_TOKEN = os.getenv('TG_TOKEN', 0)

async def main():
    bot = Bot(token=TG_TOKEN)
    dp = Dispatcher()
    
    # Включаем роутер анализатора
    dp.include_router(analyzer_router)
    
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')

# import asyncio
# import logging
# from aiogram import Bot, Dispatcher
# import os
# from dotenv import load_dotenv

# from app.handlers_analyzer import router as analyzer_router

# # Настройка логирования
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Токен бота
# load_dotenv()
# TG_TOKEN = os.getenv('TG_TOKEN',0)

# async def main():
#     dp = Dispatcher()
    
#     # Регистрируем роутер
#     dp.include_router(analyzer_router)

# if __name__ == "__main__":
#     try:
#         asyncio.run(main())
#     except KeyboardInterrupt:
#         print('Exit')