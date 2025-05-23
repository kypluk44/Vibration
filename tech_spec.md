Ниже — подробное ТЗ по фронту и бэку: разбивка на страницы, компоненты, их взаимодействие и все остальное.

⸻

1. Frontend

1.1. Общая структура
	•	Фреймворк: React + TypeScript (создание через Vite).
	•	Маршрутизация: React Router (или встроенный роутинг Next.js).
	•	State-менеджмент:
	•	Zustand для локального UI-состояния (темная тема, модалки);
	•	React Query для кэширования и синхронизации данных с API.
	•	Стили: TailwindCSS + shadcn/UI для готовых компонентов.
	•	PWA: сервис-воркеры через Workbox, пуш-уведомления (OneSignal / FCM).

⸻

1.2. Навигация и общий Layout
	•	Header
	•	Логотип «Энергогарант» (клик — на /).
	•	Иконка аватара + имя пользователя (клик — на /profile).
	•	Кнопка «Коллекции» и «Награды».
	•	Bell-иконка (уведомления).
	•	Footer
	•	Краткие ссылки (Помощь, Условия, Контакты).
	•	Main — динамический контент страниц.

⸻

1.3. Страницы и компоненты

Путь	Название страницы	Основные компоненты	Описание взаимодействия
/	Welcome / Запуск	— StartButton— AvatarPreview— BriefIntro	При клике “Начать” → POST /api/start → сохраняем avatar + profile в React Query → редирект на /scenario
/scenario	Сценарий дня	— ScenarioCard (текст, иллюстрация)— OptionButton[]	onLoad → GET /api/scenario/today → отображаем сценарий и варианты действий
/action	Обработка выбора	— ResultModal (итог, очки)— AdviceBlock (совет по страховке)	POST /api/action { scenarioId, choiceId } → Response содержит outcome, points, advice, updated streak, new collection item
/profile	Профиль пользователя	— AvatarCard— StatsPanel (очки, streak, уровень)— AchievementsList	GET /api/profile → profile + stats + achievements
/collections	Коллекции	— CollectionGrid (список предметов)— CollectionItemCard	GET /api/collections → все элементы, статус (получен/нет)
/rewards	Награды & Магазин	— RewardsList— RewardCard— RedeemButton	GET /api/rewards → перечень наград и требованияPOST /api/rewards/redeem { rewardId }
/settings	Настройки	— TogglePWA (push)— ThemeSwitch— LogoutButton	Локальная настройка PWA, темы; кнопка выхода (очищает токен)


⸻

1.4. Взаимодействие и UX-паттерны
	1.	Загрузка данных:
	•	React Query: stale-while-revalidate, дружелюбный skeleton UI.
	2.	Ошибка/Лоадер:
	•	Унифицированный ErrorBoundary + Spinner.
	3.	PWA Push:
	•	При первом заходе просим разрешение, сохраняем subscription→ backend.
	4.	Анимации:
	•	Framer Motion для переходов страниц, модалок, наград.
	5.	Мини-игры:
	•	Инкапсулируются в <MiniGame host="phaser" scenario={…} />, передаём сценарий и опции.

⸻

2. Backend

2.1. Технологии и фреймворки
	•	FastAPI (Python 3.10+)
	•	Uvicorn / Gunicorn
	•	LangGraph — каждый пользовательский агент как отдельный Graph instance
	•	Redis — хранение serialized state агентов (TTL не нужен)
	•	PostgreSQL — реляционные таблицы: users, streaks, collections, rewards, achievements
	•	Auth: JWT (FastAPI-JWT or FastAPI Users)

⸻

2.2. Основные модули
	1.	auth/
	•	POST /api/auth/register
	•	POST /api/auth/login → возвращает access_token
	•	GET /api/auth/me → профиль (id, email)
	2.	agent/
	•	POST /api/start
	•	Создаёт LangGraph-агента, генерирует avatar profile, сохраняет в Redis и PostgreSQL, возвращает avatar + initial stats.
	•	GET /api/scenario/today
	•	Загружает state из Redis, вызывает узел generate_scenario, обновляет state, отдаёт { scenarioId, text, options[] }.
	•	POST /api/action
	•	Принимает { scenarioId, choiceId }, запускает узел process_action, получает результат, advice, награды, обновляет state + БД (streak, points, collections), возвращает полный пакет данных.
	3.	profile/
	•	GET /api/profile
	•	Читает реляционные таблицы + Redis-state для динамических метрик, возвращает { avatar, streak, points, achievements[] }.
	4.	collections/
	•	GET /api/collections
	•	POST /api/collections/claim { itemId } (если нужно)
	5.	rewards/
	•	GET /api/rewards
	•	POST /api/rewards/redeem { rewardId }
	6.	notifications/
	•	POST /api/notifications/subscribe { subscription }
	•	GET /api/notifications
	•	Internal cron (или Celery beat) шлет push Reminders “streak close to reset” и “новый сценарий доступен”.

⸻

2.3. LangGraph-агент
	•	Graph nodes:
	1.	init_profile
	2.	generate_scenario(date)
	3.	process_action(scenarioId, choiceId)
	4.	generate_advice(context)
	5.	update_state(outcome, rewards, collections, streak)
	•	State schema (serializable JSON):

{
  "user_id": "...",
  "avatar": { … },
  "history": [ { "date": "2025-05-23", "scenarioId": "...", "choice": 1, "outcome": "…" } ],
  "streak": 3,
  "points": 120,
  "collections": [ "item_01", "item_02" ],
  "achievements": [ "achievement_01" ]
}


	•	Storage adapter: Redis GET/SET; backup в Postgres каждые N дней.

⸻

2.4. Бизнес-логика и правила
	•	Streak:
	•	+1 за каждый день с успешно завершённым сценарием.
	•	Если дата последнего сценария — вчера, streak сохраняется; иначе — сброс.
	•	Награды & коллекции:
	•	Таблица collections c правилами выдачи (например, день 1 → item_01).
	•	Таблица rewards с порогами (points ≥ X, streak ≥ Y).
	•	Советы:
	•	Узел generate_advice получает контекст: { profile, scenario, outcome } и возвращает краткий текст.

⸻

2.5. CI/CD и мониторинг
	•	GitHub Actions:
	•	Проверка type hints (mypy), линтинг (flake8), тесты (pytest).
	•	Docker:
	•	Отдельные контейнеры для FastAPI + Redis + Postgres.
	•	Деплой: Render.com / Fly.io / Google Cloud Run.
	•	Мониторинг: Sentry (ошибки), Prometheus + Grafana (метрики).

⸻

2.6. Пример взаимодействия “день пользователя”
	1.	06:00 (cron) Backend генерирует push каждому user_id с notification: “Сегодня новый сценарий доступен!”.
	2.	08:30 Пользователь открывает SPA → React Query автоматически fetch GET /api/scenario/today.
	3.	Сценарий отображается, пользователь выбирает действие → POST /api/action.
	4.	Backend возвращает { outcome, pointsDelta, advice, newStreak, newCollectionItem }.
	5.	Фронт — показывает ResultModal, обновляет кеш profile и collections.
	6.	Вечером пользователь заходит на /rewards — может потратить очки.

⸻

С таким детальным разделением вы получите чёткую карту работ для фронта и бэка, а также понимание точек интеграции и границ ответственности каждого модуля. Если нужны примеры схем БД, OpenAPI-спека или скелеты компонентов — дайте знать!
