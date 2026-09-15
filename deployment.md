# АвтоРесурс — Deployment Playbook (Hetzner + Atlas + Cloudflare)

**Цель:** развернуть prod от нуля до работающего HTTPS-сайта за ~30 минут.

**Итоговая архитектура:**

```
┌─────────────┐     ┌─────────────────────┐     ┌──────────────────┐
│  Cloudflare │────▶│  Hetzner VPS        │────▶│  MongoDB Atlas   │
│  DNS + CDN  │     │  autoreresurs.tech  │     │  M10 shared      │
└─────────────┘     │  ───────────────    │     │  Frankfurt (EU)  │
                    │  nginx :443         │     └──────────────────┘
                    │  frontend build     │
                    │  backend :8001      │─────▶ Emergent LLM API
                    │  supervisor         │─────▶ Resend, Telegram, Stripe
                    │  APScheduler        │
                    └─────────────────────┘
```

**Стоимость:** ~€12/мес (Hetzner CX32) + ~$60/мес (Atlas M10) + $0 (Cloudflare Free) ≈ **~$75/мес**

---

## 0. Что нужно заранее (5 мин)

- [ ] Домен: `autoresurs.tech` или что вы купите (Namecheap, Porkbun — можно без РФ карты)
- [ ] Аккаунт **Hetzner Cloud** (accounts.hetzner.com) — принимает любые VISA/Mastercard
- [ ] Аккаунт **MongoDB Atlas** (cloud.mongodb.com) — free tier, потом апгрейд
- [ ] Аккаунт **Cloudflare** (cloudflare.com) — free tier достаточно
- [ ] API-ключи заранее:
  - `EMERGENT_LLM_KEY` — из Profile → Manage plan (Emergent)
  - `RESEND_API_KEY` — из resend.com
  - `TELEGRAM_BOT_TOKEN` — от `@BotFather`
  - `STRIPE_SECRET_KEY` — из dashboard.stripe.com (test → live позже)
  - `ADMIN_JWT_SECRET` — сгенерируйте: `openssl rand -hex 32`
  - `ADMIN_MFA_SECRET_SALT` — сгенерируйте: `openssl rand -hex 32`

---

## 1. MongoDB Atlas (5 мин)

1. **Create cluster:** cloud.mongodb.com → New Project → **M10 Shared**, регион **Frankfurt (eu-central-1)**, provider AWS
2. **Network access:** Security → Network Access → Add IP → `0.0.0.0/0` (потом сузьте до IP Hetzner-сервера)
3. **Database user:** Security → Database Access → Add User → username `autoresurs`, strong password (30+ chars)
4. **Connection string:** Deployments → Connect → Drivers → Python. Копируем:
   ```
   mongodb+srv://autoresurs:<PASS>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
5. **Backup:** Deployments → Backup → включаем Continuous Backup (входит в M10)

---

## 2. Hetzner VPS (3 мин)

1. **New project** → **Add server**:
   - Location: **Falkenstein / Nuremberg** (EU)
   - Image: **Ubuntu 24.04**
   - Type: **CX32** (4 vCPU / 8 GB RAM / 80 GB SSD, €12/мес)
   - Networking: enable IPv4 + IPv6
   - SSH keys: добавьте свой ключ (Settings → Security → SSH keys → New)
   - Name: `autoresurs-prod-1`
2. Через ~30 сек получаете IP (например `159.69.123.45`)

**Firewall (Hetzner Cloud → Firewalls):** создать rule, разрешить `22/tcp` (только с вашего IP), `80/tcp` и `443/tcp` (0.0.0.0/0), закрыть всё остальное. Прикрепить к серверу.

---

## 3. Cloudflare DNS (2 мин)

1. Add site → введите `autoresurs.tech`
2. У регистратора домена меняем nameservers на те, что показал Cloudflare
3. Добавляем DNS записи:
   ```
   A     @         159.69.123.45   Proxied  (оранжевое облачко)
   A     www       159.69.123.45   Proxied
   A     api       159.69.123.45   Proxied
   ```
4. SSL/TLS → Overview → **Full (strict)**
5. SSL/TLS → Edge Certificates → Always Use HTTPS: **On**

---

## 4. Первый вход и подготовка сервера (5 мин)

```bash
ssh root@159.69.123.45
```

Обновление + установка базовых пакетов:

```bash
# Отдельный не-root пользователь
adduser --disabled-password --gecos "" deploy
usermod -aG sudo deploy
mkdir -p /home/deploy/.ssh
cp /root/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
echo "deploy ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/deploy

# Обновляем
apt-get update && apt-get -y upgrade
apt-get install -y build-essential git curl wget ufw fail2ban \
    nginx supervisor python3.11 python3.11-venv python3-pip \
    ca-certificates gnupg lsb-release

# Node.js 20 LTS + yarn
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs
npm install -g yarn

# Firewall
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Fail2ban с дефолтами уже включён для sshd
systemctl enable --now fail2ban
```

Дальше работаем от `deploy`:

```bash
su - deploy
```

---

## 5. Клонирование кода и .env (3 мин)

```bash
sudo mkdir -p /var/www && sudo chown deploy:deploy /var/www
cd /var/www
git clone https://github.com/YOURORG/autoresurs.git app
cd app
```

**Backend `.env`** (`/var/www/app/backend/.env`):

```bash
cat > /var/www/app/backend/.env <<'EOF'
MONGO_URL=mongodb+srv://autoresurs:PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
DB_NAME=autoresurs_prod

EMERGENT_LLM_KEY=sk-emergent-XXXXXXXX
RESEND_API_KEY=re_XXXXXXXXXXXXXX
RESEND_FROM_EMAIL=info@autoresurs.tech

TELEGRAM_BOT_TOKEN=1234567890:AA...
TELEGRAM_BOT_USERNAME=AutoresursBot

STRIPE_SECRET_KEY=sk_live_XXXXXX
STRIPE_WEBHOOK_SECRET=whsec_XXXXXX
STRIPE_SUCCESS_URL=https://autoresurs.tech/auto/deposit/success
STRIPE_CANCEL_URL=https://autoresurs.tech/auto/deposit/cancel

ADMIN_JWT_SECRET=<openssl rand -hex 32>
ADMIN_MFA_SECRET_SALT=<openssl rand -hex 32>

APP_BASE_URL=https://autoresurs.tech
ENVIRONMENT=production
EOF
```

**Frontend `.env`** (`/var/www/app/frontend/.env`):

```bash
cat > /var/www/app/frontend/.env <<'EOF'
REACT_APP_BACKEND_URL=https://autoresurs.tech
EOF
```

---

## 6. Backend setup (3 мин)

```bash
cd /var/www/app/backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

# Smoke check
python -c "from server import app; print('backend imports OK')"
deactivate
```

Создаём администратора вручную (одноразово):

```bash
cd /var/www/app/backend
source .venv/bin/activate
python -c "
import asyncio, os
from dotenv import load_dotenv
load_dotenv('.env')
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.hash import bcrypt
from datetime import datetime
import uuid

async def main():
    c = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = c[os.environ['DB_NAME']]
    email = 'admin@autoresurs.tech'
    pw = 'CHANGE_ME_SECURE_PASSWORD'
    doc = {
      'id': str(uuid.uuid4()),
      'email': email,
      'password_hash': bcrypt.hash(pw),
      'role': 'admin',
      'created_at': datetime.utcnow(),
    }
    await db.users.update_one({'email': email}, {'\$set': doc}, upsert=True)
    print('admin created:', email)

asyncio.run(main())
"
deactivate
```

Затем на первом входе в админку он сделает TOTP setup через `/admin/2fa/setup`.

---

## 7. Frontend build (2 мин)

```bash
cd /var/www/app/frontend
yarn install --frozen-lockfile
yarn build          # cra build → /var/www/app/frontend/build/
```

---

## 8. Supervisor: backend + scheduler (2 мин)

```bash
sudo tee /etc/supervisor/conf.d/autoresurs-backend.conf > /dev/null <<'EOF'
[program:autoresurs-backend]
command=/var/www/app/backend/.venv/bin/uvicorn server:app --host 127.0.0.1 --port 8001 --workers 2
directory=/var/www/app/backend
user=deploy
autostart=true
autorestart=true
stopsignal=TERM
stopasgroup=true
killasgroup=true
stdout_logfile=/var/log/supervisor/autoresurs-backend.out.log
stderr_logfile=/var/log/supervisor/autoresurs-backend.err.log
environment=PATH="/var/www/app/backend/.venv/bin:%(ENV_PATH)s"
EOF

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start autoresurs-backend
sudo supervisorctl status
```

⚠️ **Важно про APScheduler:** он живёт **внутри backend-процесса** и запускается через `startup`-hook. С `--workers 2` таски запускаются в обоих воркерах — дубликаты!

**Правильный вариант**: один "web" воркер (workers=2 без scheduler) + отдельный "worker" процесс:

```bash
# Вариант A (проще): один воркер, всё в нём
uvicorn server:app --host 127.0.0.1 --port 8001 --workers 1

# Вариант B (масштабируемее): гейт scheduler переменной
# Добавьте в server.py:
#   if os.getenv('RUN_SCHEDULER') == '1': scheduler.start(db)
# Тогда 2 воркера + отдельный process=scheduler в supervisor
```

**Для MVP → используйте `--workers 1`**, этого хватит на 500 concurrent пользователей.

---

## 9. Nginx + Let's Encrypt (3 мин)

```bash
sudo tee /etc/nginx/sites-available/autoresurs > /dev/null <<'EOF'
# HTTP → HTTPS redirect (Cloudflare handles the outer TLS, но локально тоже
# держим Let's Encrypt для Full-Strict).
server {
    listen 80;
    server_name autoresurs.tech www.autoresurs.tech api.autoresurs.tech;
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name autoresurs.tech www.autoresurs.tech;

    ssl_certificate     /etc/letsencrypt/live/autoresurs.tech/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/autoresurs.tech/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;

    # Frontend build
    root /var/www/app/frontend/build;
    index index.html;

    # Backend API — /api/* → uvicorn:8001
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        client_max_body_size 20M;      # deposit uploads, logos
    }

    # SPA fallback — everything else → index.html
    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    # Static assets get long cache
    location /static/ {
        expires 30d;
        add_header Cache-Control "public, max-age=2592000, immutable";
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/autoresurs /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t

# Let's Encrypt
sudo mkdir -p /var/www/certbot
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
sudo certbot --nginx -d autoresurs.tech -d www.autoresurs.tech \
  --non-interactive --agree-tos -m admin@autoresurs.tech

sudo systemctl reload nginx
```

**Проверка:**

```bash
curl -I https://autoresurs.tech
curl -s https://autoresurs.tech/api/health   # или /api/auto/fx-rate
```

---

## 10. Post-deploy checks (2 мин)

- [ ] `https://autoresurs.tech` открывается, показывает hero
- [ ] `/api/auto/vehicles?limit=1` возвращает JSON
- [ ] Пустая база — запустите первый импорт из админки:
  ```bash
  curl -X POST https://autoresurs.tech/api/auto/admin/sources/import-all \
    -H "Authorization: Bearer <ADMIN_JWT>" -H "x-admin-mfa: <MFA_TOKEN>"
  ```
- [ ] Через 5 минут проверьте: `curl https://autoresurs.tech/api/auto/vehicles?limit=1`
- [ ] Scheduler статус: `curl https://autoresurs.tech/api/auto/admin/scheduler/status`

---

## 11. Мониторинг и бэкапы

**Логи** (в реальном времени):
```bash
sudo tail -f /var/log/supervisor/autoresurs-backend.err.log
sudo tail -f /var/log/nginx/access.log
```

**Ротация:** уже включена (`/etc/logrotate.d/nginx`, `/etc/logrotate.d/supervisor`).

**MongoDB backup:** Atlas делает Continuous Backup сам. Дополнительно можно раз в сутки `mongodump`:

```bash
sudo tee /etc/cron.daily/mongodump > /dev/null <<'EOF'
#!/bin/bash
BACKUP_DIR=/var/backups/mongo
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d)
mongodump --uri "$(grep MONGO_URL /var/www/app/backend/.env | cut -d= -f2)" \
  --out $BACKUP_DIR/$DATE --gzip
find $BACKUP_DIR -type d -mtime +14 -exec rm -rf {} +
EOF
sudo chmod +x /etc/cron.daily/mongodump
```

**Uptime monitoring:** UptimeRobot free tier — ping `https://autoresurs.tech/api/auto/fx-rate` каждые 5 минут.

---

## 12. Update workflow (после первого деплоя)

```bash
ssh deploy@autoresurs.tech
cd /var/www/app
git pull
# backend
cd backend && source .venv/bin/activate && pip install -r requirements.txt && deactivate
# frontend
cd ../frontend && yarn install --frozen-lockfile && yarn build
# restart
sudo supervisorctl restart autoresurs-backend
sudo systemctl reload nginx
```

Автоматизируйте позже через GitHub Actions → deploy webhook.

---

## 13. Что оставили на потом (не критично для запуска)

- **Playwright fleet** для Intel Phase 2 — вынести на отдельную ноду `CPX21`, когда буду включать live Simulcast
- **CDN для картинок** — сейчас Cloudflare проксирует SPA целиком, для 1000+ фото добавьте отдельный bucket (R2 free 10GB) + subdomain `img.autoresurs.tech`
- **Sentry** для error tracking — `pip install sentry-sdk` + `SENTRY_DSN` в .env
- **GA4 / Yandex.Metrica** — тег в `frontend/public/index.html`
- **Emergent Object Storage** для deposit-proofs и logo-uploads (сейчас в Mongo, лимит 16MB на doc)

---

## 14. Troubleshooting

| Симптом | Причина | Фикс |
|---|---|---|
| `502 Bad Gateway` | backend упал | `sudo supervisorctl status autoresurs-backend` + смотрим логи |
| `Cannot connect to MongoDB` | Atlas IP whitelist | добавьте IP сервера в Atlas → Network Access |
| Emails не приходят | Resend domain не верифицирован | Resend → Domains → добавьте `autoresurs.tech`, SPF/DKIM записи в Cloudflare |
| APScheduler дубликаты | `--workers > 1` | переключитесь на `--workers 1` или гейт-переменную |
| SSL error после Cloudflare | Mode `Flexible` вместо `Full (strict)` | Cloudflare → SSL/TLS → Full (strict) |
| Slow catalog | Missing indexes | `mongosh` → `db.auto_vehicles.createIndex({make:1, model:1, year:1, status:1})` |

---

## 15. Оценка времени

| Шаг | Минуты |
|---|--:|
| 0. Prep | 5 |
| 1. Atlas | 5 |
| 2. Hetzner | 3 |
| 3. Cloudflare | 2 |
| 4. Server prep | 5 |
| 5. Code + .env | 3 |
| 6. Backend install | 3 |
| 7. Frontend build | 2 |
| 8. Supervisor | 2 |
| 9. Nginx + SSL | 3 |
| 10. Post-checks | 2 |
| **Итого** | **~35 мин** |

Если всё уже настроено и вы просто хотите передеплоить — шаги 5→8 занимают 2 минуты.
