# ffmpeg_path = "C:\\ffmpeg\\ffmpeg-master-latest-win64-gpl-shared\\bin\\ffmpeg.exe"

# import os
# import tempfile
# import speech_recognition as sr
# from aiogram import Router, F
# from aiogram.types import Message
# from pydub import AudioSegment
# from pydub.silence import split_on_silence
# from generate import ai_analyze_message, analyze_long_text, simple_text_analysis
# import logging
# import subprocess
# import hashlib
# import time
# from collections import defaultdict
# import re
# import asyncio

# router = Router()
# logger = logging.getLogger(__name__)

# # Кэш и ограничения
# text_cache = {}
# user_requests = defaultdict(list)
# last_ai_error = defaultdict(float)

# def parse_analysis_response(response: str) -> dict:
#     """Парсит ответ от AI на основную мысль и ответ с улучшенной обработкой"""
#     if not response:
#         return {
#             "main_idea": "Не удалось проанализировать сообщение", 
#             "answer": "Попробуйте отправить сообщение еще раз"
#         }
    
#     # Очищаем ответ
#     response = response.strip()
    
#     # Случай 1: Ищем стандартный формат с разделением по строкам
#     lines = response.split('\n')
#     main_idea = ""
#     answer = ""
    
#     for line in lines:
#         line = line.strip()
#         if line.startswith('ОСНОВНАЯ МЫСЛЬ:'):
#             main_idea = line.replace('ОСНОВНАЯ МЫСЛЬ:', '').strip()
#         elif line.startswith('ОТВЕТ:'):
#             answer = line.replace('ОТВЕТ:', '').strip()
    
#     # Случай 2: Если нашли оба поля, но они в одной строке
#     if not answer and 'ОТВЕТ:' in response:
#         parts = response.split('ОТВЕТ:')
#         if len(parts) == 2:
#             main_part = parts[0]
#             if 'ОСНОВНАЯ МЫСЛЬ:' in main_part:
#                 main_idea = main_part.split('ОСНОВНАЯ МЫСЛЬ:')[1].strip()
#             else:
#                 main_idea = main_part.strip()
#             answer = parts[1].strip()
    
#     # Случай 3: Если все еще не нашли, пытаемся разделить по другим признакам
#     if not main_idea and not answer:
#         parts = response.split('\n\n')
#         if len(parts) >= 2:
#             main_idea = parts[0]
#             answer = parts[1]
#         else:
#             sentences = [s.strip() for s in response.split('.') if s.strip()]
#             if len(sentences) >= 2:
#                 main_idea = '. '.join(sentences[:min(2, len(sentences))]) + '.'
#                 remaining = sentences[min(2, len(sentences)):]
#                 if remaining:
#                     answer = '. '.join(remaining[:min(3, len(remaining))]) + '.'
#                 else:
#                     answer = "Интересная история! Расскажите больше подробностей."
#             else:
#                 main_idea = response
#                 answer = "Понимаю вашу ситуацию. Давайте обсудим это подробнее."
    
#     # Очищаем от возможных остатков не-русского текста
#     main_idea = re.sub(r'[^\u0400-\u04FF\s\.\,\!\?\-\:\(\)\d]', '', main_idea)
#     answer = re.sub(r'[^\u0400-\u04FF\s\.\,\!\?\-\:\(\)\d]', '', answer)
    
#     # Удаляем лишние пробелы
#     main_idea = re.sub(r'\s+', ' ', main_idea).strip()
#     answer = re.sub(r'\s+', ' ', answer).strip()
    
#     # Удаляем возможные остатки меток
#     for label in ['ОСНОВНАЯ МЫСЛЬ:', 'ОТВЕТ:']:
#         main_idea = main_idea.replace(label, '').strip()
#         answer = answer.replace(label, '').strip()
    
#     # Проверяем, что поля не пустые
#     if not main_idea:
#         main_idea = "Основная мысль не выделена"
#     if not answer:
#         answer = "Не удалось сгенерировать ответ"
    
#     # Обрезаем слишком длинные ответы
#     if len(main_idea) > 500:
#         main_idea = main_idea[:497] + "..."
#     if len(answer) > 500:
#         answer = answer[:497] + "..."
    
#     return {"main_idea": main_idea, "answer": answer}

# def can_make_ai_request(user_id: int) -> bool:
#     """Проверяет, можно ли делать запрос к AI"""
#     now = time.time()
    
#     user_requests[user_id] = [req_time for req_time in user_requests[user_id] if now - req_time < 120]
#     if len(user_requests[user_id]) >= 3:
#         return False
    
#     if now - last_ai_error.get(user_id, 0) < 300:
#         return False
    
#     return True

# def add_request(user_id: int):
#     """Добавляет запрос в историю пользователя"""
#     user_requests[user_id].append(time.time())

# def mark_ai_error(user_id: int):
#     """Отмечает ошибку AI для пользователя"""
#     last_ai_error[user_id] = time.time()

# def split_audio_on_silence(audio_path, silence_thresh=-40, min_silence_len=1000, chunk_length=30000):
#     """
#     Разбивает аудио на сегменты по тишине или по времени
#     """
#     try:
#         # Загружаем аудио
#         audio = AudioSegment.from_wav(audio_path)
#         duration = len(audio)
        
#         # Если аудио короткое, возвращаем как есть
#         if duration <= 45000:  # 45 секунд
#             return [audio]
        
#         # Сначала пытаемся разбить по тишине
#         chunks = split_on_silence(
#             audio,
#             min_silence_len=min_silence_len,
#             silence_thresh=silence_thresh,
#             keep_silence=500  # Оставляем немного тишины для естественности
#         )
        
#         # Если разбиение по тишине не дало результатов или слишком много/мало чанков,
#         # разбиваем по фиксированному времени
#         if not chunks or len(chunks) > 20 or len(chunks) < 2:
#             chunks = []
#             for i in range(0, duration, chunk_length):
#                 chunk = audio[i:i + chunk_length]
#                 if len(chunk) > 1000:  # Минимальная длина чанка 1 секунда
#                     chunks.append(chunk)
        
#         logger.info(f"Аудио разбито на {len(chunks)} сегментов, общая длительность: {duration}мс")
#         return chunks
        
#     except Exception as e:
#         logger.error(f"Ошибка при разбиении аудио: {e}")
#         # В случае ошибки возвращаем весь файл как один чанк
#         return [AudioSegment.from_wav(audio_path)]

# async def recognize_long_audio(wav_filename):
#     """Распознает длинные аудио файлы, разбивая их на сегменты"""
#     recognizer = sr.Recognizer()
#     full_text = ""
    
#     try:
#         # Разбиваем аудио на сегменты
#         chunks = split_audio_on_silence(wav_filename)
        
#         if len(chunks) > 1:
#             logger.info(f"Обрабатываю {len(chunks)} сегментов аудио")
        
#         for i, chunk in enumerate(chunks):
#             # Создаем временный файл для сегмента
#             with tempfile.NamedTemporaryFile(delete=False, suffix=f'_segment_{i}.wav') as segment_file:
#                 segment_filename = segment_file.name
            
#             # Экспортируем сегмент
#             chunk.export(segment_filename, format="wav")
            
#             try:
#                 # Распознаем сегмент
#                 with sr.AudioFile(segment_filename) as source:
#                     recognizer.adjust_for_ambient_noise(source, duration=0.5)
#                     audio_data = recognizer.record(source)
#                     segment_text = recognizer.recognize_google(audio_data, language='ru-RU')
                    
#                     if segment_text:
#                         full_text += segment_text + " "
#                         logger.info(f"Сегмент {i+1}/{len(chunks)} распознан: {segment_text[:50]}...")
#                     else:
#                         logger.warning(f"Сегмент {i+1} не распознан")
                        
#             except sr.UnknownValueError:
#                 logger.warning(f"Не удалось распознать сегмент {i+1}")
#             except Exception as e:
#                 logger.error(f"Ошибка при распознавании сегмента {i+1}: {e}")
#             finally:
#                 # Удаляем временный файл сегмента
#                 if os.path.exists(segment_filename):
#                     os.unlink(segment_filename)
        
#         return full_text.strip()
        
#     except Exception as e:
#         logger.error(f"Ошибка при распознавании длинного аудио: {e}")
#         # Пробуем распознать как обычное короткое аудио
#         try:
#             with sr.AudioFile(wav_filename) as source:
#                 recognizer.adjust_for_ambient_noise(source, duration=0.5)
#                 audio_data = recognizer.record(source)
#                 return recognizer.recognize_google(audio_data, language='ru-RU')
#         except:
#             return ""

# @router.message(F.voice)
# async def handle_voice_message(message: Message):
#     """Обработка голосовых сообщений с поддержкой длинных записей"""
#     user_id = message.from_user.id
    
#     if not can_make_ai_request(user_id):
#         await message.answer("⏳ Слишком много запросов. Подождите 2-3 минуты.")
#         return
    
#     add_request(user_id)
    
#     # Проверяем длину голосового сообщения
#     voice_duration = message.voice.duration
#     if voice_duration > 120:
#         await message.answer(f"🎤 Обрабатываю длинное голосовое сообщение ({voice_duration} сек)... Это может занять некоторое время.")
#     else:
#         await message.answer("🎤 Обрабатываю голосовое сообщение...")
    
#     ogg_filename = None
#     wav_filename = None
    
#     try:
#         voice = message.voice
#         file = await message.bot.get_file(voice.file_id)
#         file_path = file.file_path
        
#         # Создаем временные файлы
#         with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as ogg_file:
#             ogg_filename = ogg_file.name
        
#         with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as wav_file:
#             wav_filename = wav_file.name
        
#         # Скачиваем файл
#         await message.bot.download_file(file_path, ogg_filename)
        
#         if not os.path.exists(ogg_filename) or os.path.getsize(ogg_filename) == 0:
#             await message.answer("❌ Не удалось скачать голосовое сообщение")
#             return
        
#         # Конвертируем OGG в WAV
#         ffmpeg_path = "C:\\ffmpeg\\ffmpeg-master-latest-win64-gpl-shared\\bin\\ffmpeg.exe"
        
#         if not os.path.exists(ffmpeg_path):
#             await message.answer("❌ FFmpeg не найден")
#             return
        
#         try:
#             result = subprocess.run([
#                 ffmpeg_path,
#                 '-i', ogg_filename,
#                 '-acodec', 'pcm_s16le',
#                 '-ac', '1',
#                 '-ar', '16000',
#                 '-af', 'volume=1.5,highpass=f=200,lowpass=f=3000',
#                 wav_filename,
#                 '-y'
#             ], capture_output=True, text=True, timeout=60)
            
#             if result.returncode != 0:
#                 await message.answer("❌ Ошибка конвертации аудио")
#                 return
                
#         except subprocess.TimeoutExpired:
#             await message.answer("❌ Таймаут конвертации аудио")
#             return
        
#         # Проверяем что WAV файл создан
#         if not os.path.exists(wav_filename) or os.path.getsize(wav_filename) == 0:
#             await message.answer("❌ Не удалось конвертировать аудио")
#             return
        
#         # Распознаем аудио
#         text = await recognize_long_audio(wav_filename)
        
#         if not text or len(text.strip()) < 5:
#             await message.answer("❌ Не удалось распознать речь в сообщении")
#             return
        
#         text_length = len(text)

#         # ОБНОВЛЕНИЕ: Разбиваем длинный текст на части для отправки
#         if text_length > 4000:
#             chunks = split_long_text(text)
#             await message.answer(f"📝 Распознанный текст ({text_length} символов, отправляется {len(chunks)} частями):")
            
#             # Отправляем части с задержкой между сообщениями
#             for i, chunk in enumerate(chunks):
#                 # Добавляем номер части к каждому сообщению
#                 part_text = f"**Часть {i+1}/{len(chunks)}:**\n{chunk}"
                
#                 # Дополнительная проверка длины
#                 if len(part_text) > 4096:
#                     # Если все равно слишком длинное, разбиваем еще мельче
#                     sub_chunks = split_long_text(chunk, max_length=2000)
#                     for j, sub_chunk in enumerate(sub_chunks):
#                         sub_part_text = f"**Часть {i+1}.{j+1}:**\n{sub_chunk}"
#                         await message.answer(sub_part_text)
#                         await asyncio.sleep(0.5)  # Задержка между сообщениями
#                 else:
#                     await message.answer(part_text)
#                     await asyncio.sleep(0.5)  # Задержка между сообщениями
#         else:
#             await message.answer(f"📝 Распознанный текст ({text_length} символов):\n{text}")
        
#         # Проверяем кэш
#         text_hash = hashlib.md5(text.encode()).hexdigest()
#         if text_hash in text_cache:
#             analysis = text_cache[text_hash]
#             await message.answer("♻️ Использую кэшированный результат")
#         else:
#             # Пытаемся использовать AI для анализа
#             try:
#                 # Выбираем метод анализа в зависимости от длины текста
#                 if text_length > 4000:
#                     await message.answer("📖 Текст длинный, анализирую по частям...")
#                     analysis_response = await analyze_long_text(text)
#                 else:
#                     analysis_response = await ai_analyze_message(text)
                
#                 # Логируем сырой ответ от AI для отладки
#                 logger.info(f"Сырой ответ от AI: {analysis_response}")
                
#                 analysis = parse_analysis_response(analysis_response)
#                 text_cache[text_hash] = analysis
                
#                 # Очищаем старые записи кэша
#                 if len(text_cache) > 50:
#                     oldest_key = next(iter(text_cache))
#                     text_cache.pop(oldest_key)
                    
#             except Exception as e:
#                 logger.error(f"AI анализ не удался: {e}")
#                 mark_ai_error(user_id)
#                 # Используем резервный анализ
#                 backup_response = await simple_text_analysis(text)
#                 analysis = parse_analysis_response(backup_response)
#                 await message.answer("⚠️ Использую локальный анализ (AI временно недоступен)")
        
#         # Сначала отправляем основную мысль
#         await message.answer(f"🎯 **Основная мысль:**\n{analysis['main_idea']}")
        
#         # Затем отправляем заголовок "Готовый ответ для отправки"
#         await message.answer("💬 **Готовый ответ для отправки:**")
        
#         # Затем отправляем сам ответ отдельным сообщением
#         await message.answer(analysis['answer'])
        
#     except sr.RequestError as e:
#         await message.answer("❌ Ошибка сервиса распознавания речи.")
#         logger.error(f"Speech recognition error: {e}")
#     except Exception as e:
#         error_msg = str(e)
#         logger.error(f"Voice processing error: {e}")
        
#         if "429" in error_msg or "rate" in error_msg.lower():
#             mark_ai_error(user_id)
#             await message.answer("❌ Лимиты AI исчерпаны. Попробуйте через 5-10 минут.")
#         elif "Не удалось получить ответ" in error_msg:
#             mark_ai_error(user_id)
#             await message.answer("❌ Сервис AI временно недоступен. Использую локальный анализ.")
#             try:
#                 # Используем резервный анализ
#                 backup_response = await simple_text_analysis(text)
#                 analysis = parse_analysis_response(backup_response)
#                 await message.answer(f"🎯 **Основная мысль:**\n{analysis['main_idea']}")
#                 await message.answer("💬 **Готовый ответ для отправки:**")
#                 await message.answer(analysis['answer'])
#             except:
#                 await message.answer("❌ Не удалось обработать сообщение.")
#         elif "message is too long" in error_msg.lower():
#             # Обработка слишком длинных сообщений - разбиваем на части
#             chunks = split_long_text(text)
#             await message.answer("📝 Распознанный текст (отправляется частями):")
#             for i, chunk in enumerate(chunks):
#                 await message.answer(f"**Часть {i+1}/{len(chunks)}:**\n{chunk}")
#         else:
#             await message.answer(f"❌ Ошибка обработки: {error_msg}")
#     finally:
#         # Удаляем временные файлы
#         for filename in [ogg_filename, wav_filename]:
#             if filename and os.path.exists(filename):
#                 try:
#                     os.unlink(filename)
#                 except Exception as e:
#                     logger.warning(f"Не удалось удалить файл {filename}: {e}")

# @router.message(F.text & ~F.command)
# async def handle_text_message(message: Message):
#     """Обработка текстовых сообщений с поддержкой длинных текстов"""
#     user_id = message.from_user.id
#     text = message.text
    
#     if not can_make_ai_request(user_id):
#         await message.answer("⏳ Слишком много запросов. Подождите 2-3 минуты.")
#         return
    
#     add_request(user_id)
    
#     text_length = len(text)
    
#     # Уведомление о длинном тексте
#     if text_length > 4000:
#         await message.answer(f"📖 Обрабатываю длинный текст ({text_length} символов)... Это может занять некоторое время.")
#     else:
#         await message.answer("🤔 Анализирую текст...")
    
#     try:
#         # Проверяем кэш
#         text_hash = hashlib.md5(text.encode()).hexdigest()
#         if text_hash in text_cache:
#             analysis = text_cache[text_hash]
#             await message.answer("♻️ Использую кэшированный результат")
#         else:
#             # Пытаемся использовать AI для анализа
#             try:
#                 # Выбираем метод анализа в зависимости от длины текста
#                 if text_length > 4000:
#                     analysis_response = await analyze_long_text(text)
#                 else:
#                     analysis_response = await ai_analyze_message(text)
                
#                 # Логируем сырой ответ от AI для отладки
#                 logger.info(f"Сырой ответ от AI (текст): {analysis_response}")
                
#                 analysis = parse_analysis_response(analysis_response)
#                 text_cache[text_hash] = analysis
#             except Exception as e:
#                 logger.error(f"AI анализ не удался: {e}")
#                 mark_ai_error(user_id)
#                 # Используем резервный анализ
#                 backup_response = await simple_text_analysis(text)
#                 analysis = parse_analysis_response(backup_response)
#                 await message.answer("⚠️ Использую локальный анализ (AI временно недоступен)")
#             except Exception as e:
#                 error_msg = str(e)
#                 logger.error(f"Text processing error: {e}")
                
#                 if "429" in error_msg or "rate" in error_msg.lower():
#                     mark_ai_error(user_id)
#                     await message.answer("❌ Лимиты AI исчерпаны. Попробуйте через 5-10 минут.")
#                 elif "Не удалось получить ответ" in error_msg:
#                     mark_ai_error(user_id)
#                     await message.answer("❌ Сервис AI временно недоступен.")
#                 elif "message is too long" in error_msg.lower():
#                     # Если ответ слишком длинный, разбиваем его на гарантированно маленькие части
#                     response_text = f"🎯 **Основная мысль:**\n{analysis['main_idea']}\n\n💬 **Готовый ответ для отправки:**\n{analysis['answer']}"
#                     chunks = split_long_text(response_text, max_length=1500)
#                     for chunk in chunks:
#                         await message.answer(chunk[:4096])  # Дополнительная защита
#                         await asyncio.sleep(0.3)
#                 else:
#                     await message.answer(f"❌ Ошибка при анализе сообщения: {error_msg}")
        
#         # Сначала отправляем основную мысль
#         await message.answer(f"🎯 **Основная мысль:**\n{analysis['main_idea']}")
        
#         # Затем отправляем заголовок "Готовый ответ для отправки"
#         await message.answer("💬 **Готовый ответ для отправки:**")
        
#         # Затем отправляем сам ответ отдельным сообщением
#         await message.answer(analysis['answer'])
        
#     except Exception as e:
#         error_msg = str(e)
#         logger.error(f"Text processing error: {e}")
        
#         if "429" in error_msg or "rate" in error_msg.lower():
#             mark_ai_error(user_id)
#             await message.answer("❌ Лимиты AI исчерпаны. Попробуйте через 5-10 минут.")
#         elif "Не удалось получить ответ" in error_msg:
#             mark_ai_error(user_id)
#             await message.answer("❌ Сервис AI временно недоступен.")
#         elif "message is too long" in error_msg.lower():
#         # Обработка слишком длинных сообщений - разбиваем на части с улучшенной логикой
#             chunks = split_long_text(text, max_length=2000)
#             await message.answer(f"📝 Распознанный текст ({len(text)} символов, отправляется {len(chunks)} частями):")
            
#             for i, chunk in enumerate(chunks):
#                 part_text = f"**Часть {i+1}/{len(chunks)}:**\n{chunk}"
                
#                 # Двойная проверка длины
#                 if len(part_text) > 4096:
#                     # Экстренное разбиение
#                     emergency_chunks = [part_text[j:j+2000] for j in range(0, len(part_text), 2000)]
#                     for emergency_chunk in emergency_chunks:
#                         await message.answer(emergency_chunk[:4096])
#                         await asyncio.sleep(0.5)
#                 else:
#                     await message.answer(part_text)
#                     await asyncio.sleep(0.5)
#         else:
#             await message.answer(f"❌ Ошибка при анализе сообщения: {error_msg}")

# @router.message(F.command("start"))
# async def start_command(message: Message):
#     """Обработка команды /start"""
#     welcome_text = """
# 🤖 **Бот-анализатор сообщений**

# Отправьте мне:
# • 📝 Текстовое сообщение (ЛЮБОЙ длины)
# • 🎤 Голосовое сообщение (ЛЮБОЙ длины)

# Я:
# 1. 📝 Распознаю текст (для голосовых)
# 2. 🎯 Выделю основную мысль  
# 3. 💬 Предложу готовый ответ

# ✨ **Особенности:**
# - ✅ Поддержка ОЧЕНЬ длинных сообщений
# - ✅ Автоматическое разбиение на части
# - ✅ Точное сохранение деталей
# - ✅ Удобное копирование ответов

# ⚠️ *Ограничения:*
# - Максимум 3 запросов в 2 минуты
# - При ошибках AI используется локальный анализ

# 💡 *Советы:*
# - Можно отправлять сообщения любой длины!
# - Бот сам разобьет длинные тексты на части
# - Ответы отправляются отдельными сообщениями для удобства
#     """
#     await message.answer(welcome_text)

# @router.message(F.command("help"))
# async def help_command(message: Message):
#     """Помощь по использованию бота"""
#     help_text = """
# 📋 **Как использовать бота:**

# 💬 *Текстовые сообщения:*
# - Просто напишите сообщение любой длины
# - Бот выделит основную мысль и предложит готовый ответ

# 🎤 *Голосовые сообщения:*
# - Отправьте голосовое сообщение любой длины
# - Бот распознает речь и проанализирует содержание

# 📊 *Что вы получите:*
# 1. **Распознанный текст** (для голосовых)
# 2. **Основную мысль** - краткое содержание сообщения  
# 3. **Готовый ответ** - отдельным сообщением, легко копируется

# ⚡ *Ограничения:*
# - Максимум 3 запроса каждые 2 минуты
# - При ошибках AI используется упрощенный анализ

# 🛠 *Команды:*
# /start - начать работу
# /help - эта справка
# /status - статус системы
# /clear_cache - очистить кэш
#     """
#     await message.answer(help_text)

# @router.message(F.command("status"))
# async def status_command(message: Message):
#     """Показывает статус лимитов"""
#     user_id = message.from_user.id
#     now = time.time()
    
#     # Статус запросов
#     recent_requests = [req_time for req_time in user_requests[user_id] if now - req_time < 120]
#     remaining_requests = max(0, 3 - len(recent_requests))
    
#     # Статус AI
#     ai_blocked = now - last_ai_error.get(user_id, 0) < 300
#     ai_status = "🔴 Временно отключен" if ai_blocked else "🟢 Доступен"
    
#     status_text = f"""
# 📊 **Статус системы:**

# 🔄 Запросы: {len(recent_requests)}/3 (осталось: {remaining_requests})
# 🤖 AI: {ai_status}
# 💾 Кэш: {len(text_cache)} записей

# {"⏳ AI будет доступен через " + str(int(300 - (now - last_ai_error[user_id]))) + " сек" if ai_blocked else "✅ Все системы работают"}
#     """
#     await message.answer(status_text)

# @router.message(F.command("clear_cache"))
# async def clear_cache_command(message: Message):
#     """Очищает кэш"""
#     text_cache.clear()
#     await message.answer("✅ Кэш очищен")

# @router.message(F.command("reset_limits"))
# async def reset_limits_command(message: Message):
#     """Сбрасывает лимиты для пользователя (для тестирования)"""
#     user_id = message.from_user.id
#     user_requests[user_id] = []
#     last_ai_error[user_id] = 0
#     await message.answer("✅ Лимиты сброшены")

# def split_long_text(text: str, max_length: int = 3900) -> list:
#     """Разбивает длинный текст на части для отправки в Telegram"""
#     if len(text) <= max_length:
#         return [text]
    
#     chunks = []
#     current_chunk = ""
    
#     # Разбиваем текст на предложения
#     sentences = re.split(r'([.!?]+[\s]*)', text)
    
#     # Объединяем разделители с предложениями
#     sentences_combined = []
#     for i in range(0, len(sentences), 2):
#         if i + 1 < len(sentences):
#             sentences_combined.append(sentences[i] + sentences[i + 1])
#         else:
#             sentences_combined.append(sentences[i])
    
#     for sentence in sentences_combined:
#         # Если текущее предложение само по себе слишком длинное, разбиваем его
#         if len(sentence) > max_length:
#             # Разбиваем длинное предложение на части
#             words = sentence.split()
#             temp_chunk = ""
            
#             for word in words:
#                 if len(temp_chunk) + len(word) + 1 <= max_length:
#                     if temp_chunk:
#                         temp_chunk += " " + word
#                     else:
#                         temp_chunk = word
#                 else:
#                     if temp_chunk:
#                         chunks.append(temp_chunk)
#                     temp_chunk = word
            
#             if temp_chunk:
#                 chunks.append(temp_chunk)
#         else:
#             # Обычное предложение
#             if len(current_chunk) + len(sentence) <= max_length:
#                 current_chunk += sentence
#             else:
#                 if current_chunk:
#                     chunks.append(current_chunk.strip())
#                 current_chunk = sentence
    
#     if current_chunk:
#         chunks.append(current_chunk.strip())
    
#     return chunks

import os
import tempfile
import speech_recognition as sr
from aiogram import Router, F
from aiogram.types import Message
from pydub import AudioSegment
from pydub.silence import split_on_silence
import logging
import subprocess
import hashlib
import time
from collections import defaultdict
import re
from aiogram.filters import Command
from app.generate import ai_analyze_message, analyze_long_text, simple_text_analysis

router = Router()
logger = logging.getLogger(__name__)

# Кэш и ограничения
text_cache = {}
user_requests = defaultdict(list)
last_ai_error = defaultdict(float)

@router.message(Command("start"))
async def start_command(message: Message):
    """Обработка команды /start"""
    welcome_text = "Привет! Рад тебя видеть. Как я могу помочь?"
    await message.answer(welcome_text)
    logger.info(f"✅ Обработана команда /start от пользователя {message.from_user.id}")

@router.message(Command("help"))
async def help_command(message: Message):
    """Помощь по использованию бота"""
    help_text = "Просто отправьте мне текстовое или голосовое сообщение для анализа"
    await message.answer(help_text)

@router.message(Command("status"))
async def status_command(message: Message):
    """Показывает статус"""
    await message.answer("✅ Бот работает")

# Остальные функции и обработчики...

def parse_analysis_response(response: str) -> dict:
    """Парсит ответ от AI на основную мысль и ответ с улучшенной обработкой"""
    if not response:
        return {
            "main_idea": "Не удалось проанализировать сообщение", 
            "answer": "Попробуйте отправить сообщение еще раз"
        }
    
    # Очищаем ответ
    response = response.strip()
    
    # Случай 1: Ищем стандартный формат с разделением по строкам
    lines = response.split('\n')
    main_idea = ""
    answer = ""
    
    for line in lines:
        line = line.strip()
        if line.startswith('ОСНОВНАЯ МЫСЛЬ:'):
            main_idea = line.replace('ОСНОВНАЯ МЫСЛЬ:', '').strip()
        elif line.startswith('ОТВЕТ:'):
            answer = line.replace('ОТВЕТ:', '').strip()
    
    # Случай 2: Если нашли оба поля, но они в одной строке
    if not answer and 'ОТВЕТ:' in response:
        parts = response.split('ОТВЕТ:')
        if len(parts) == 2:
            main_part = parts[0]
            if 'ОСНОВНАЯ МЫСЛЬ:' in main_part:
                main_idea = main_part.split('ОСНОВНАЯ МЫСЛЬ:')[1].strip()
            else:
                main_idea = main_part.strip()
            answer = parts[1].strip()
    
    # Случай 3: Если все еще не нашли, пытаемся разделить по другим признакам
    if not main_idea and not answer:
        parts = response.split('\n\n')
        if len(parts) >= 2:
            main_idea = parts[0]
            answer = parts[1]
        else:
            sentences = [s.strip() for s in response.split('.') if s.strip()]
            if len(sentences) >= 2:
                main_idea = '. '.join(sentences[:min(2, len(sentences))]) + '.'
                remaining = sentences[min(2, len(sentences)):]
                if remaining:
                    answer = '. '.join(remaining[:min(3, len(remaining))]) + '.'
                else:
                    answer = "Интересная история! Расскажите больше подробностей."
            else:
                main_idea = response
                answer = "Понимаю вашу ситуацию. Давайте обсудим это подробнее."
    
    # Очищаем от возможных остатков не-русского текста
    main_idea = re.sub(r'[^\u0400-\u04FF\s\.\,\!\?\-\:\(\)\d]', '', main_idea)
    answer = re.sub(r'[^\u0400-\u04FF\s\.\,\!\?\-\:\(\)\d]', '', answer)
    
    # Удаляем лишние пробелы
    main_idea = re.sub(r'\s+', ' ', main_idea).strip()
    answer = re.sub(r'\s+', ' ', answer).strip()
    
    # Удаляем возможные остатки меток
    for label in ['ОСНОВНАЯ МЫСЛЬ:', 'ОТВЕТ:']:
        main_idea = main_idea.replace(label, '').strip()
        answer = answer.replace(label, '').strip()
    
    # Проверяем, что поля не пустые
    if not main_idea:
        main_idea = "Основная мысль не выделена"
    if not answer:
        answer = "Не удалось сгенерировать ответ"
    
    # Обрезаем слишком длинные ответы
    if len(main_idea) > 500:
        main_idea = main_idea[:497] + "..."
    if len(answer) > 500:
        answer = answer[:497] + "..."
    
    return {"main_idea": main_idea, "answer": answer}

def can_make_ai_request(user_id: int) -> bool:
    """Проверяет, можно ли делать запрос к AI"""
    now = time.time()
    
    user_requests[user_id] = [req_time for req_time in user_requests[user_id] if now - req_time < 120]
    if len(user_requests[user_id]) >= 3:
        return False
    
    if now - last_ai_error.get(user_id, 0) < 300:
        return False
    
    return True

def add_request(user_id: int):
    """Добавляет запрос в историю пользователя"""
    user_requests[user_id].append(time.time())

def mark_ai_error(user_id: int):
    """Отмечает ошибку AI для пользователя"""
    last_ai_error[user_id] = time.time()

def split_audio_on_silence(audio_path, silence_thresh=-40, min_silence_len=1000, chunk_length=30000):
    """
    Разбивает аудио на сегменты по тишине или по времени
    """
    try:
        # Загружаем аудио
        audio = AudioSegment.from_wav(audio_path)
        duration = len(audio)
        
        # Если аудио короткое, возвращаем как есть
        if duration <= 45000:  # 45 секунд
            return [audio]
        
        # Сначала пытаемся разбить по тишине
        chunks = split_on_silence(
            audio,
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh,
            keep_silence=500  # Оставляем немного тишины для естественности
        )
        
        # Если разбиение по тишине не дало результатов или слишком много/мало чанков,
        # разбиваем по фиксированному времени
        if not chunks or len(chunks) > 20 or len(chunks) < 2:
            chunks = []
            for i in range(0, duration, chunk_length):
                chunk = audio[i:i + chunk_length]
                if len(chunk) > 1000:  # Минимальная длина чанка 1 секунда
                    chunks.append(chunk)
        
        logger.info(f"Аудио разбито на {len(chunks)} сегментов, общая длительность: {duration}мс")
        return chunks
        
    except Exception as e:
        logger.error(f"Ошибка при разбиении аудио: {e}")
        # В случае ошибки возвращаем весь файл как один чанк
        return [AudioSegment.from_wav(audio_path)]

async def recognize_long_audio(wav_filename):
    """Распознает длинные аудио файлы, разбивая их на сегменты"""
    recognizer = sr.Recognizer()
    full_text = ""
    
    try:
        # Разбиваем аудио на сегменты
        chunks = split_audio_on_silence(wav_filename)
        
        if len(chunks) > 1:
            logger.info(f"Обрабатываю {len(chunks)} сегментов аудио")
        
        for i, chunk in enumerate(chunks):
            # Создаем временный файл для сегмента
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'_segment_{i}.wav') as segment_file:
                segment_filename = segment_file.name
            
            # Экспортируем сегмент
            chunk.export(segment_filename, format="wav")
            
            try:
                # Распознаем сегмент
                with sr.AudioFile(segment_filename) as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio_data = recognizer.record(source)
                    segment_text = recognizer.recognize_google(audio_data, language='ru-RU')
                    
                    if segment_text:
                        full_text += segment_text + " "
                        logger.info(f"Сегмент {i+1}/{len(chunks)} распознан: {segment_text[:50]}...")
                    else:
                        logger.warning(f"Сегмент {i+1} не распознан")
                        
            except sr.UnknownValueError:
                logger.warning(f"Не удалось распознать сегмент {i+1}")
            except Exception as e:
                logger.error(f"Ошибка при распознавании сегмента {i+1}: {e}")
            finally:
                # Удаляем временный файл сегмента
                if os.path.exists(segment_filename):
                    os.unlink(segment_filename)
        
        return full_text.strip()
        
    except Exception as e:
        logger.error(f"Ошибка при распознавании длинного аудио: {e}")
        # Пробуем распознать как обычное короткое аудио
        try:
            with sr.AudioFile(wav_filename) as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio_data = recognizer.record(source)
                return recognizer.recognize_google(audio_data, language='ru-RU')
        except:
            return ""

@router.message(F.voice)
async def handle_voice_message(message: Message):
    """Обработка голосовых сообщений с поддержкой длинных записей"""
    user_id = message.from_user.id
    
    if not can_make_ai_request(user_id):
        await message.answer("⏳ Слишком много запросов. Подождите 2-3 минуты.")
        return
    
    add_request(user_id)
    
    # Проверяем длину голосового сообщения
    voice_duration = message.voice.duration
    if voice_duration > 120:
        await message.answer(f"🎤 Обрабатываю длинное голосовое сообщение ({voice_duration} сек)... Это может занять некоторое время.")
    else:
        await message.answer("🎤 Обрабатываю голосовое сообщение...")
    
    ogg_filename = None
    wav_filename = None
    
    try:
        voice = message.voice
        file = await message.bot.get_file(voice.file_id)
        file_path = file.file_path
        
        # Создаем временные файлы
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as ogg_file:
            ogg_filename = ogg_file.name
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as wav_file:
            wav_filename = wav_file.name
        
        # Скачиваем файл
        await message.bot.download_file(file_path, ogg_filename)
        
        if not os.path.exists(ogg_filename) or os.path.getsize(ogg_filename) == 0:
            await message.answer("❌ Не удалось скачать голосовое сообщение")
            return
        
        # Конвертируем OGG в WAV
        ffmpeg_path = "C:\\ffmpeg\\ffmpeg-master-latest-win64-gpl-shared\\bin\\ffmpeg.exe"
        
        if not os.path.exists(ffmpeg_path):
            await message.answer("❌ FFmpeg не найден")
            return
        
        try:
            result = subprocess.run([
                ffmpeg_path,
                '-i', ogg_filename,
                '-acodec', 'pcm_s16le',
                '-ac', '1',
                '-ar', '16000',
                '-af', 'volume=1.5,highpass=f=200,lowpass=f=3000',
                wav_filename,
                '-y'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                await message.answer("❌ Ошибка конвертации аудио")
                return
                
        except subprocess.TimeoutExpired:
            await message.answer("❌ Таймаут конвертации аудио")
            return
        
        # Проверяем что WAV файл создан
        if not os.path.exists(wav_filename) or os.path.getsize(wav_filename) == 0:
            await message.answer("❌ Не удалось конвертировать аудио")
            return
        
        # Распознаем аудио
        text = await recognize_long_audio(wav_filename)
        
        if not text or len(text.strip()) < 5:
            await message.answer("❌ Не удалось распознать речь в сообщении")
            return
        
        text_length = len(text)
        await message.answer(f"📝 Распознанный текст ({text_length} символов):\n{text}")
        
        # Проверяем кэш
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in text_cache:
            analysis = text_cache[text_hash]
            await message.answer("♻️ Использую кэшированный результат")
        else:
            # Пытаемся использовать AI для анализа
            try:
                from generate import ai_analyze_message, analyze_long_text, simple_text_analysis
                
                # Выбираем метод анализа в зависимости от длины текста
                if text_length > 4000:
                    await message.answer("📖 Текст длинный, анализирую по частям...")
                    analysis_response = await analyze_long_text(text)
                else:
                    analysis_response = await ai_analyze_message(text)
                
                # Логируем сырой ответ от AI для отладки
                logger.info(f"Сырой ответ от AI: {analysis_response}")
                
                analysis = parse_analysis_response(analysis_response)
                text_cache[text_hash] = analysis
                
                # Очищаем старые записи кэша
                if len(text_cache) > 50:
                    oldest_key = next(iter(text_cache))
                    text_cache.pop(oldest_key)
                    
            except Exception as e:
                logger.error(f"AI анализ не удался: {e}")
                mark_ai_error(user_id)
                # Используем резервный анализ
                from generate import simple_text_analysis
                backup_response = await simple_text_analysis(text)
                analysis = parse_analysis_response(backup_response)
                await message.answer("⚠️ Использую локальный анализ (AI временно недоступен)")
        
        # Сначала отправляем основную мысль
        await message.answer(f"🎯 **Основная мысль:**\n{analysis['main_idea']}")
        
        # Затем отправляем заголовок "Готовый ответ для отправки"
        await message.answer("💬 **Готовый ответ для отправки:**")
        
        # Затем отправляем сам ответ отдельным сообщением
        await message.answer(analysis['answer'])
        
    except sr.RequestError as e:
        await message.answer("❌ Ошибка сервиса распознавания речи.")
        logger.error(f"Speech recognition error: {e}")
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Voice processing error: {e}")
        
        if "429" in error_msg or "rate" in error_msg.lower():
            mark_ai_error(user_id)
            await message.answer("❌ Лимиты AI исчерпаны. Попробуйте через 5-10 минут.")
        elif "Не удалось получить ответ" in error_msg:
            mark_ai_error(user_id)
            await message.answer("❌ Сервис AI временно недоступен. Использую локальный анализ.")
            try:
                from generate import simple_text_analysis
                backup_response = await simple_text_analysis(text)
                analysis = parse_analysis_response(backup_response)
                await message.answer(f"🎯 **Основная мысль:**\n{analysis['main_idea']}")
                await message.answer("💬 **Готовый ответ для отправки:**")
                await message.answer(analysis['answer'])
            except:
                await message.answer("❌ Не удалось обработать сообщение.")
        else:
            await message.answer(f"❌ Ошибка обработки: {error_msg}")
    finally:
        # Удаляем временные файлы
        for filename in [ogg_filename, wav_filename]:
            if filename and os.path.exists(filename):
                try:
                    os.unlink(filename)
                except Exception as e:
                    logger.warning(f"Не удалось удалить файл {filename}: {e}")

@router.message(F.text & ~F.command)
async def handle_text_message(message: Message):
    """Обработка текстовых сообщений с поддержкой длинных текстов"""
    user_id = message.from_user.id
    text = message.text
    
    # Игнорируем команды, которые уже обработаны другими хендлерами
    if text.startswith('/'):
        return
    
    if not can_make_ai_request(user_id):
        await message.answer("⏳ Слишком много запросов. Подождите 2-3 минуты.")
        return
    
    add_request(user_id)
    
    text_length = len(text)
    
    if text_length > 4000:
        await message.answer(f"📖 Обрабатываю длинный текст ({text_length} символов)... Это может занять некоторое время.")
    else:
        await message.answer("🤔 Анализирую текст...")
    
    try:
        # Проверяем кэш
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in text_cache:
            analysis = text_cache[text_hash]
            await message.answer("♻️ Использую кэшированный результат")
        else:
            # Пытаемся использовать AI для анализа
            try:
                from generate import ai_analyze_message, analyze_long_text, simple_text_analysis
                
                # Выбираем метод анализа в зависимости от длины текста
                if text_length > 4000:
                    analysis_response = await analyze_long_text(text)
                else:
                    analysis_response = await ai_analyze_message(text)
                
                # Логируем сырой ответ от AI для отладки
                logger.info(f"Сырой ответ от AI (текст): {analysis_response}")
                
                analysis = parse_analysis_response(analysis_response)
                text_cache[text_hash] = analysis
            except Exception as e:
                logger.error(f"AI анализ не удался: {e}")
                mark_ai_error(user_id)
                # Используем резервный анализ
                from generate import simple_text_analysis
                backup_response = await simple_text_analysis(text)
                analysis = parse_analysis_response(backup_response)
                await message.answer("⚠️ Использую локальный анализ (AI временно недоступен)")
        
        # Сначала отправляем основную мысль
        await message.answer(f"🎯 **Основная мысль:**\n{analysis['main_idea']}")
        
        # Затем отправляем заголовок "Готовый ответ для отправки"
        await message.answer("💬 **Готовый ответ для отправки:**")
        
        # Затем отправляем сам ответ отдельным сообщением
        await message.answer(analysis['answer'])
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Text processing error: {e}")
        
        if "429" in error_msg or "rate" in error_msg.lower():
            mark_ai_error(user_id)
            await message.answer("❌ Лимиты AI исчерпаны. Попробуйте через 5-10 минут.")
        elif "Не удалось получить ответ" in error_msg:
            mark_ai_error(user_id)
            await message.answer("❌ Сервис AI временно недоступен.")
        else:
            await message.answer(f"❌ Ошибка при анализе сообщения: {error_msg}")
            