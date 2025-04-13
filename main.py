import asyncio
import os
import sys
from typing import Dict, Tuple, Set

from dotenv import load_dotenv
from telethon import TelegramClient, events
from PyCharacterAI import Client as CharacterAIClient, get_client
from PyCharacterAI.exceptions import SessionClosedError

# ========== НАСТРОЙКА ==========
# Загрузка переменных окружения из .env файла
load_dotenv('.env')

# Проверка обязательных переменных окружения
required_vars = [
    'TELEGRAM_API_ID',
    'TELEGRAM_API_HASH',
    'CHARACTER_AI_TOKEN',
    'CHARACTER_AI_ID',
    'ALLOWED_USERNAMES',
    'ALLOWED_USER_IDS'
]

for var in required_vars:
    if not os.getenv(var):
        raise ValueError(f"Необходимо указать {var} в .env файле")

# Настройка event loop policy для Windows
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


# ========== КОНФИГУРАЦИЯ ==========
class Config:
    TELEGRAM_API_ID = int(os.getenv('TELEGRAM_API_ID'))
    TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
    CHARACTER_AI_TOKEN = os.getenv('CHARACTER_AI_TOKEN')
    CHARACTER_AI_ID = os.getenv('CHARACTER_AI_ID')

    @staticmethod
    def get_allowed_usernames() -> Set[str]:
        return set(username.strip() for username in os.getenv('ALLOWED_USERNAMES').split(','))

    @staticmethod
    def get_allowed_user_ids() -> Set[int]:
        return set(int(user_id.strip()) for user_id in os.getenv('ALLOWED_USER_IDS').split(','))


# ========== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ==========
user_chats: Dict[int, Tuple[CharacterAIClient, object]] = {}  # {user_id: (client, chat)}
character_lock = asyncio.Lock()  # Блокировка для потокобезопасности

# Инициализация Telegram клиента
tg_client = TelegramClient(
    'session_name',
    Config.TELEGRAM_API_ID,
    Config.TELEGRAM_API_HASH,
    system_version='4.16.30-vxCUSTOM'
)


async def get_character_response(user_id: int, prompt: str) -> str:
    """
    Получает ответ от Character AI для конкретного пользователя

    Args:
        user_id (int): ID пользователя Telegram
        prompt (str): Текст запроса

    Returns:
        str: Ответ от Character AI или сообщение об ошибке
    """
    # Блокировка для избежания конкурентных запросов
    async with character_lock:
        try:
            # Если у пользователя ещё нет чата, создаём новый
            if user_id not in user_chats:
                client = await get_client(token=Config.CHARACTER_AI_TOKEN)
                chat, greeting = await client.chat.create_chat(Config.CHARACTER_AI_ID)
                user_chats[user_id] = (client, chat)
                print(f"Создан новый чат для пользователя {user_id}. Приветствие: {greeting.get_primary_candidate().text}")

            client, chat = user_chats[user_id]
            answer = await client.chat.send_message(
                Config.CHARACTER_AI_ID,
                chat.chat_id,
                prompt
            )
            return answer.get_primary_candidate().text

        except SessionClosedError:
            # Попытка восстановить сессию при ошибке
            try:
                print(f"Сессия для пользователя {user_id} закрыта, создаем новую...")
                client = await get_client(token=Config.CHARACTER_AI_TOKEN)
                chat, _ = await client.chat.create_chat(Config.CHARACTER_AI_ID)
                user_chats[user_id] = (client, chat)

                answer = await client.chat.send_message(
                    Config.CHARACTER_AI_ID,
                    chat.chat_id,
                    prompt
                )
                return answer.get_primary_candidate().text
            except Exception as e:
                print(f"Ошибка восстановления сессии для {user_id}: {e}")
                return "Произошла ошибка соединения. Попробуйте позже."

        except Exception as e:
            print(f"Ошибка Character AI для пользователя {user_id}: {e}")
            return "Извините, произошла ошибка. Попробуйте позже."


@tg_client.on(events.NewMessage(incoming=True))
async def handle_message(event: events.NewMessage.Event) -> None:
    """
    Обработчик входящих сообщений в Telegram.

    Args:
        event (events.NewMessage.Event): Событие нового сообщения
    """
    sender = await event.get_sender()

    # Проверка прав доступа пользователя
    if (sender.id not in Config.get_allowed_user_ids() and
            (not sender.username or sender.username not in Config.get_allowed_usernames())):
        return

    # Логирование входящего сообщения
    user_msg = event.raw_text
    print(f'Сообщение от {sender.username or sender.id}: {user_msg}')

    # Получение и отправка ответа
    reply = await get_character_response(sender.id, user_msg)
    await event.reply(reply)

async def initialize_telegram_client() -> bool:
    """
    Инициализирует Telegram клиент и авторизует пользователя.

    Returns:
        bool: True если инициализация прошла успешно, иначе False
    """
    try:
        await tg_client.connect()

        if not await tg_client.is_user_authorized():
            await tg_client.send_code_request(str(Config.TELEGRAM_API_ID))
            phone = input('Введите телефон: ')
            await tg_client.sign_in(phone)
            code = input('Введите код: ')
            await tg_client.sign_in(phone, code)

        return True

    except Exception as e:
        print(f"Ошибка инициализации Telegram клиента: {e}")
        return False


async def cleanup_chats():
    """Закрывает все активные сессии Character AI."""
    async with character_lock:
        for user_id, (client, _) in list(user_chats.items()):
            try:
                await client.close_session()
                print(f"Закрыта сессия для пользователя {user_id}")
            except Exception as e:
                print(f"Ошибка при закрытии сессии {user_id}: {e}")
            finally:
                user_chats.pop(user_id, None)


async def main() -> None:
    """
    Основная функция, управляющая жизненным циклом приложения.
    """
    try:
        # Инициализация Telegram клиента
        if not await initialize_telegram_client():
            raise RuntimeError("Не удалось инициализировать Telegram клиент")

        print("Бот успешно запущен и готов к работе...")
        await tg_client.run_until_disconnected()

    except Exception as e:
        print(f"Критическая ошибка: {e}")
    finally:
        # Корректное завершение работы
        # Закрываем все чаты
        await cleanup_chats()

        if tg_client.is_connected():
            await tg_client.disconnect()
            print("Telegram клиент отключен.")


if __name__ == '__main__':
    try:
        # Запуск основного цикла
        with tg_client:
            tg_client.loop.run_until_complete(main())

    except KeyboardInterrupt:
        print("\nБот остановлен пользователем")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
    finally:
        print("Работа бота завершена.")
