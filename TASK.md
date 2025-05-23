Полное техническое задание (ТЗ) для веб-игры «ЭнергоГород» 1.0

(добавлена новая механика № 11 — «Сюжетные главы»)

⸻

0. Глоссарий
	•	Игрок — физическое лицо с действующим аккаунтом «ЭНЕРГОГАРАНТ».
	•	Сессия — период между логином и логаутом либо закрытием вкладки > 30 мин.
	•	Токены — виртуальная валюта «Энерготокен».
	•	Событие — единица интерактива (погодный шторм, AI-квиз и т. д.).
	•	Продукт — страховой полис/пакет компании.
	•	Купон — JSON-объект с правилами скидки, подписанный JWT-ключом-приложения.

⸻

1. Область применения

Игровой Web-модуль призван:
	1.	Увеличить частоту посещений экосистемы «ЭНЕРГОГАРАНТ» минимум до DAU/MAU = 0,25.
	2.	Повысить кросс-продажи не-авто продуктов ≥ 10 % за 6 месяцев.
	3.	Поддерживать A/B-маркетинг без релиза клиентского кода.

⸻

2. Архитектура верхнего уровня

 ┌───────────────┐                               ┌──────────────┐
 │  Frontend SPA │ ←JWT→ ┌────────┐  REST/WebSocket │  Game-Core MS │
 │ Next.js +     │       │  Auth   │───────────────▶│  (NestJS)     │
 │  Phaser 4     │       └────────┘                └───────┬───────┘
 └─────▲─────────┘                                 ▲       │Redis
       │WS/PubSub                                  │       │Streams
       │                                           │       ▼
┌──────┴─────────┐                           ┌──────────────┐
│  AI-Service    │◀──gRPC──OpenAI/LLM        │ Analytics MS │→ ClickHouse
│ (Python/FastAPI│                           └──────────────┘
└───────────────┘

Все сервисы упакованы в Docker, оркестрация — YC Managed K8s.

⸻

3. Модуль «Профиль»

3.1. Данные игрока (PostgreSQL schema public)

users
┌─ id (UUID, PK)
├─ eg_uid (VARCHAR, uniq)  -- ID в ядре "ЭНЕРГОГАРАНТ"
├─ email, phone
├─ avatar_url
├─ locale (ENUM)
├─ created_at, updated_at

user_stats
┌─ user_id (FK users.id)
├─ level INT
├─ xp INT
├─ energy INT
├─ token_balance INT
├─ last_login TIMESTAMP

3.2. API

GET /profile/me            ↔ 200 JSON(users + stats)
PATCH /profile/avatar      {file} → 202
POST /auth/sso             {eg_jwt} → game_jwt

3.3. Безопасность
	•	SSO-JWT шифруется RSA-256, срок — 24 ч.
	•	Сквозная роль RBAC: player, moderator, admin.

⸻

4. Модуль «Карта»

4.1. Техническое устройство
	•	Canvas/WebGL движок — Phaser 4 в режиме isometric grid 8×8; тайл = 128 px.
	•	Lazy-chunk загрузка ассетов (esbuild code-split, CDN smax-age = 30 дней).

4.2. ДАННЫЕ (PostgreSQL map)

plots
┌ id SERIAL PK
├ user_id FK
├ type ENUM('house','car','sport','travel','office')
├ level INT (1-10)
├ pos_x, pos_y INT

4.3. Взаимодействие
	•	Клик по тайлу → modal /<type>/panel (React Portal).
	•	Улучшение стоит energy + tokens ↔ POST /map/upgrade.
	•	Каждой постройке соответствует продукт-щит (см. гл. 5).

⸻

5. Интеграция со страховыми продуктами

Сущность в игре	Продукт «ЭНЕРГОГАРАНТ»	Триггер покупки
house	Имущество, титул	шторм/пожар
car	ОСАГО, КАСКО	ДТП/угон
sport	НС-спорт, телемедицина	травма
travel	Travel-polis	задержка рейса
office	ДМС мигрантов, НС	травма сотруд.

5.1. Каталог
	•	Единый REST /products (идентичен боевому API).
	•	Маппинг хранится в таблице product_link(plot_type, product_id).

5.2. UX-поток покупки
	1.	Игрок жмёт «Защитить» → открывается iframe оферты https://pay.energogarant.ru/?product=<id>&utm=game.
	2.	После успешного платежа CRM шлёт webhook /payment/success → + токены, эвент purchase в ClickHouse.

⸻

6. Механики вовлечения

(⭐ — новая механика № 11)

№	Название	TL;DR
1	Дневная «Энерго-Рулетка»	1 бесплатный спин/24 ч
2	Real-time погодные ивенты	Штормы по MeteoAPI
3	Сезонный Battle Pass	40 уровней/60 дней
4	Лидерборды & PvE-рейды	Топ-100 + «катастрофа»
5	AR-охота за кристаллами	WebAR + POI
6	AI-квиз «Разбери кейс»	сценарии GPT
7	Виртуальная валюта	«Энерготокены»
8	NFT-бейджи (опция)	mint on TON
9	Flash-распродажи	-15 % / 1 час
10	Микро-игры внутри зданий	Tap-runner, парковка
11⭐	Сюжетные главы	Story-campaign на 5 эпизодов

6.1. Полная спецификация каждой механики

Формат: Functional → Data/API → Acceptance

1. Энерго-Рулетка
	•	Functional: доступно с уровня 1; 1 спин/сутки; платный re-spin = 50 токенов.
	•	API: POST /wheel/spin → {sector_id, prize}; лог в daily_spin (PK user_id+date).
	•	Acceptance: 90 % ответов ≤ 300 мс, неконсистент ≤ 0,1 %.

2. Погодные ивенты
	•	Functional: MeteoAPI + geo‐hash игрока; не чаще 1/день/регион.
	•	Data: Redis Stream weather:<region> → Front overlay.
	•	Acceptance: пуш должен прийти ≤ 5 мин после Webhook.

3. Battle Pass
	•	Functional: 40 уровней, награды JSON-список.
	•	Data: таблица bp_progress(user_id, level, xp).
	•	Acceptance: купон выдаётся сразу при апе уровня.

4. Лидерборд/Рейды
	•	Functional: рейтинг по total_xp; рейд каждое вс 18:00 UTC+3.
	•	API: Redis ZADD leaderboard:xp.
	•	Acceptance: сортировка по убыванию XP корректна в 95 % запросов.

5. AR-охота
	•	Functional: активна 08-22 лок.время; открывает карту, отрисовывает 3 кристалла/день.
	•	Data: poi_locations(lat,lng,radius_m,partner_id).
	•	Acceptance: SST < 2 с на 4G, трекинг 30 fps.

6. AI-квиз
	•	Functional: 3 вопроса, 60 с таймер; ≥ 2 правильных — купон.
	•	API: POST /quiz/start → gRPC AI; ответы пишутся в quiz_answers.
	•	Acceptance: генерация квиза ≤ 1,5 с.

7. Валюта
	•	Functional: базовый курс — 1 ₽ = 10 токенов.
	•	Data: token_tx(id, user_id, delta, src); баланс в user_stats.
	•	Acceptance: двойное списание ≤ 0,001 %.

8. NFT-бейдж
	•	Functional: mint TON; gas оплачивает компания.
	•	Data: nft_mints(token_id, user_id, tx_hash).
	•	Acceptance: hash сохраняется ≤ 5 с после mint.

9. Flash-sale
	•	Functional: фича-флаг sale_active; таймер 60 мин.
	•	API: GET /sale/current; купон JWT exp = 24 ч.
	•	Acceptance: время сервера и клиента не расходится > 500 мс.

10. Микро-игры
	•	Functional: 2 mini-scene на здании; таблица mini_scores.
	•	Data: event score_submit → Redis pubsub.
	•	Acceptance: fps ≥ 45 на среднем Android.

11. ⭐ Сюжетные главы (НОВАЯ)
	•	Functional: линейная кампанией на 5 эпизодов (каждый — интерактивный комикс + выбор).
	•	Доступ к следующей главе после прохождения квиза уровня сложности «Medium».
	•	Завершение каждой главы — выдача тематического скина здания и купона на соответствующий продукт.
	•	AI: GPT-сценарист генерирует диалоги на основе профиля игрока.
	•	Data:

story_progress
┌ user_id FK
├ chapter INT
├ completed_at TIMESTAMP


	•	API:

POST /story/start {chapter}
POST /story/choice {chapter, node_id, option}
GET  /story/state


	•	Acceptance:
	•	Лоадинг главы ≤ 2 с на 4G.
	•	Выдача купона после финального узла — 100 % гарантирована.
	•	Повторное прохождение выдаёт только косметический рескин, купон не дублируется.

⸻

7. AI-Service

7.1. Стек
	•	Python 3.12 + FastAPI, модель по-умолчанию — GPT-4o via Azure OpenAI; fallback — локальная Llama 3-70B в GGUF через vLLM.
	•	Кэш Redis TTL = 6 ч по hash(prompt).

7.2. Схема Prompt’ов

{
  "user_profile": { "has_car": true, "travel_freq": "high" },
  "context": "weather_event",
  "need": ["risk", "probability", "description", "product_hint"]
}

7.3. SLA
	•	P95 latency ≤ 1200 мс.
	•	Тест на токсичность — Perspective API score < 0,15.

⸻

8. Аналитика

Событие	Парам-ры	Хранилище
login	device, locale	ClickHouse events
wheel_spin	sector, prize	idem
purchase	product_id, price, token_bonus	idem
story_finish	chapter	idem

Дашборды в Yandex DataLens, обновление stream < 30 с.

⸻

9. НФТ (non-functional) требования
	•	Производительность: 3 500 RPS на кластер (3 pod’а game-core), P95 < 300 мс.
	•	Доступность: 99,8 % мес.
	•	GDPR/152-ФЗ: персональные данные → отдельный users_pd (YC CMK-encrypted).
	•	Accessibility: WCAG 2.1 AA для публичных страниц.

⸻

10. Тестирование и QA
	1.	Unit — coverage ≥ 80 %.
	2.	E2E — Playwright, сценарии: регистрация, рулетка, покупка полиса.
	3.	Load — k6, цель 3 500 RPS.
	4.	Security — OWASP ZAP, статический анализ SonarQube.

⸻

11. CI / CD
	•	GitHub Actions → Docker build → YC Container Registry.
	•	Helm-chart ver =app.semver → blue-green deploy.
	•	Rollback one-click в Argo CD.

⸻

12. План внедрения

Неделя	Этап
1-2	Auth, профиль, карта MVP
3-4	Мех. 1, 2, 3
5-6	Интеграция продуктов, купоны
7-8	Мех. 4, 5, 6, AI-service
9-10	Новая механика 11 + open beta
11	Load-test, баг-фиксы
12	Production release


⸻

Итог: документ описывает полный цикл разработки версии 1.0, покрывает все ключевые аспекты (данные, API, механики, безопасность, DevOps). Новая сюжетная кампания (механика № 11) расширяет эмоциональное ядро и связывает страховые продукты с личными историями клиента, усиливая вовлечённость и кросс-продажи.
