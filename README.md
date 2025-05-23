# Telegram + Character AI Бот

Бот, соединяющий Telegram с Character AI, позволяющий пользователям общаться с ИИ-персонажами через Telegram.

## Особенности

- Индивидуальные чаты для каждого пользователя
- Белый список разрешенных пользователей
- Устойчивое соединение с автоматическим восстановлением
- Поддержка групповых чатов (если добавить в `ALLOWED_USER_IDS` / `ALLOWED_USERNAMES`)

---

## Запуск бота

### Предварительные требования

- Python 3.9+
- Telegram API ID и Hash
- Character AI токен доступа
- Character AI ID персонажа

---

### Установка

1. Клонируйте репозиторий:

```bash
git clone https://github.com/ваш-репозиторий.git
cd ваш-репозиторий
```

2. Установите все необходимые зависимости:

```bash
pip install -r requirements.txt
```

3. Получение Telegram API ID и Hash:
   1. Перейдите на my.telegram.org
   2. Авторизуйтесь под своим аккаунтом Telegram
   3. Выберите "API development tools"
   4. Заполните форму (можно указать любые корректные данные):
      - App title: MyCharacterAIBot
      - Short name: charbot
      - URL: (можно оставить пустым)
      - Platform: Web
   5. После создания получите:
      - api_id → TELEGRAM_API_ID
      - api_hash → TELEGRAM_API_HASH
   6. Добавьте в .env:
      ```bash
      TELEGRAM_API_ID=ваш_id_числом
      TELEGRAM_API_HASH=ваш_hash_строка
      ```
4. Получение Character AI токен доступа:      
   1. Войдите на character.ai
   2. Откройте DevTools (F12, Ctrl + Shift + I)
   3. Перейдите во вкладку Network
   4. Нажмите ctrl+f и введите в поиске authorization и поищите среди найденных совпадений вкладку в которой будет содержаться "Authorization Token" и значение после Token скопируйте в .env:
      ```bash
        CHARACTER_AI_TOKEN=скопированный_токен
      ```

5. Получение Character AI ID персонажа:      
   1. Найдите нужного персонажа на character.ai
   2. Перейдите в чат с ним
   3. Скопируйте ID из URL (часть после chat/)
   4. Добавьте в .env:
      ```bash
        CHARACTER_AI_ID=ABCDE12345
      ```

6. Настройте белый список пользователей:      
   - Чтобы получить Telegram ID:
     1. Напишите боту @userinfobot или перешлите сообщение нужного пользователя
     2. Он ответит сообщением с ID отправителя сообщения
   - Чтобы узнать username:
     1. Откройте профиль пользователя Telegram
     2. Скопируйте Username @username
   - Добавьте в .env (если что боту хватит чего-то одного, либо юзернейма либо айди):
      ```bash
        ALLOWED_USER_IDS=123456789,987654321
        ALLOWED_USERNAMES=username1,username2
      ```
  
  7. Запустите бота:
      ```bash
        python main.py
      ```
   - При первом запуске:
     1. Введите номер телефона в международном формате
     2. Введите код подтверждения из Telegram
     3. Создастся файл session_name.session (хранит данные авторизации) и бот запустится
   - При последующих запусках авторизация не потребуется
   - Когда бот запустится, то вы увидете сообщение об этом в консоли
   - Также вы можете отслеживать сообщения пользователей в консоли
   - Для завершения работы просто остановите выполнение кода
