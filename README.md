# 🚀 NexusVPN — Коммерческая VPN Экосистема (Marzban Xray VLESS + Reality)

Полнофункциональная продакшн-экосистема для независимого коммерческого VPN-сервиса:
- **Backend:** Python (FastAPI), SQLAlchemy 2.0 Async, Pydantic v2
- **Telegram Bot:** aiogram 3.x с поддержкой реферальных ссылок (`/start ref_xxx`) и WebApp кнопки
- **Telegram Mini App:** Tailwind CSS + Alpine.js с киберпанк/дарк UI, живым таймером, выбором локаций, QR-кодом и реферальной системой
- **VPN Core:** Интеграция с панелью **Marzban** (протоколы VLESS + Reality + XTLS Vision) по REST API
- **Клиенты для пользователей:** Happ Proxy Utility (iOS/Android), AmneziaVPN (Windows/macOS/Linux), v2rayNG (Android), Streisand / Shadowrocket (iOS).

---

## 📁 Структура проекта

```text
├── database.py         # Подключение к БД (SQLite aiosqlite / PostgreSQL asyncpg), Base, get_db()
├── models.py           # Модели User, Subscription, Referral
├── marzban_client.py   # Async httpx клиент Marzban API (токены, создание, продление, блокировка)
├── main.py             # FastAPI REST API (криптографическая валидация HMAC WebApp, тарифы, рефералы)
├── bot.py              # aiogram 3.x Telegram-бот
├── frontend/
│   └── index.html      # Telegram Mini App на Alpine.js + Tailwind
├── requirements.txt    # Зависимости Python
├── .env.example        # Пример переменных окружения
├── docker-compose.yml  # Готовый стек Docker
└── Dockerfile          # Сборка контейнера
```

---

## 🛠️ Пошаговая инструкция по развертыванию на сервере (Ubuntu 22.04 / 24.04)

### Шаг 1: Подготовка сервера и установка Marzban

Если у вас еще не установлена панель Marzban:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl socat git ufw

# Установка официального скрипта Marzban
sudo bash -c "$(curl -sL https://github.com/Gozargah/Marzban-scripts/raw/master/marzban.sh)" @ install

# Создание первого администратора Marzban:
marzban cli admin create --sudo
```
*Запомните логин и пароль администратора Marzban, они понадобятся для `.env`.*

---

### Шаг 2: Клонирование и настройка окружения

1. Установите Python 3.10+ и pip:
```bash
sudo apt install -y python3 python3-pip python3-venv
```

2. Склонируйте проект в каталог `/opt/nexusvpn`:
```bash
sudo mkdir -p /opt/nexusvpn
sudo chown -R $USER:$USER /opt/nexusvpn
cd /opt/nexusvpn
# Скопируйте файлы проекта сюда
```

3. Создайте виртуальное окружение и установите зависимости:
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

4. Создайте файл боевых настроек `.env`:
```bash
cp .env.example .env
nano .env
```
Заполните параметры:
```ini
BOT_TOKEN=123456789:AAH...Ваш_токен_от_BotFather
BOT_USERNAME=NexusVpnBot
MARZBAN_HOST=https://marzban.yourdomain.com:8000
MARZBAN_USERNAME=admin
MARZBAN_PASSWORD=ваш_пароль_админа_marzban
WEBAPP_URL=https://vpn.yourdomain.com/static/index.html
DATABASE_URL=sqlite+aiosqlite:///./vpn_service.db
```

---

### Шаг 3: Настройка Telegram-бота в @BotFather

1. Откройте `@BotFather` в Telegram.
2. Создайте нового бота командой `/newbot`.
3. Включите WebApp Menu Button:
   - Отправьте `/setmenubutton`
   - Выберите вашего бота
   - Введите URL Mini App: `https://vpn.yourdomain.com/static/index.html`
   - Введите текст кнопки: `⚡ Nexus VPN`
4. Включите Inline-режим: `/setinline` -> Enable.

---

### Шаг 4: Настройка Nginx и SSL (Certbot)

Установите Nginx и Certbot:
```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

Создайте конфигурационный файл `/etc/nginx/sites-available/nexusvpn.conf`:
```nginx
server {
    server_name vpn.yourdomain.com;

    # Проксирование FastAPI и статики Mini App
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Активируйте сайт и выпустите SSL-сертификат:
```bash
sudo ln -s /etc/nginx/sites-available/nexusvpn.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d vpn.yourdomain.com
```

---

### Шаг 5: Настройка автозапуска через Systemd

Создайте сервис для FastAPI бэкенда `/etc/systemd/system/nexus-api.service`:
```ini
[Unit]
Description=NexusVPN FastAPI Backend
After=network.target

[Service]
User=root
WorkingDirectory=/opt/nexusvpn
ExecStart=/opt/nexusvpn/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=5
EnvironmentFile=/opt/nexusvpn/.env

[Install]
WantedBy=multi-user.target
```

Создайте сервис для aiogram Telegram-бота `/etc/systemd/system/nexus-bot.service`:
```ini
[Unit]
Description=NexusVPN Telegram Bot
After=network.target

[Service]
User=root
WorkingDirectory=/opt/nexusvpn
ExecStart=/opt/nexusvpn/venv/bin/python bot.py
Restart=always
RestartSec=5
EnvironmentFile=/opt/nexusvpn/.env

[Install]
WantedBy=multi-user.target
```

Активируйте и запустите оба сервиса:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nexus-api
sudo systemctl enable --now nexus-bot

# Проверка статуса
sudo systemctl status nexus-api
sudo systemctl status nexus-bot
```

---

### Шаг 6: (Альтернатива) Запуск через Docker Compose

Если вы предпочитаете Docker:
```bash
docker-compose up -d --build
docker-compose logs -f
```

---

## 🔒 Безопасность и проверка работоспособности

1. **Криптографическая проверка HMAC-SHA256:**
   Бэкенд в `main.py` проверяет подлинность `initData` по официальному протоколу Telegram с ключом `WebAppData + BOT_TOKEN`.
2. **Бесплатный тест:**
   Каждому новому аккаунту доступен 1 раз тестовый период на 3 дня. Повторная выдача блокируется на уровне БД и Marzban.
3. **Реферальный цикл:**
   Когда пользователь переходит по ссылке `https://t.me/NexusVpnBot?start=ref_xxxx`, в БД связываются аккаунты. При совершении первой покупки реферер мгновенно получает 100 ₽ + 15% на баланс.
