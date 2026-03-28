# Настройка Supabase для Inferno Grade Tracker

Кратко: создаёте проект в Supabase, таблицу `profiles`, ключи кладёте в переменные окружения (или временно в `modules/cloud_profile.py` как `_DEFAULT_URL` / `_DEFAULT_KEY` только для отладки).

## 1. Проект и ключи

1. Зайдите на [https://supabase.com](https://supabase.com) и создайте проект.
2. В разделе **Project Settings → API** скопируйте:
   - **Project URL** → переменная окружения `INFERNO_SUPABASE_URL`
   - **anon public** или **service_role** → `INFERNO_SUPABASE_KEY`

Рекомендация для десктопного .exe: для первых тестов можно использовать **anon** с открытыми политиками RLS (см. ниже). Для продакшена лучше защищать строки политиками или выносить запись прогресса в Edge Function с секретом.

## 2. SQL таблицы `profiles`

В **SQL Editor** выполните:

```sql
create table if not exists public.profiles (
  id uuid primary key default gen_random_uuid(),
  fio text not null,
  fio_key text not null unique,
  nickname text not null,
  gold int not null default 0,
  keys int not null default 0,
  -- счётчик двоек (историческое имя колонки total_fives сохраняем для совместимости)
  total_fives int not null default 0,
  title text not null default '',
  is_cheater boolean not null default false,
  cheater_until timestamptz null,
  -- снимок «накрученного» локального состояния на момент флага читера (аудит / отладка)
  cheat_local_snapshot jsonb null,
  -- последние доверенные значения из облака на момент наказания
  legit_cloud_snapshot jsonb null,
  -- скрыть строку из публичного лидерборда (админ / тестовый аккаунт)
  is_admin boolean not null default false
);

create index if not exists profiles_total_fives_idx
  on public.profiles (total_fives desc);

alter table public.profiles enable row level security;
```

Если таблица уже создана без JSON-полей, добавьте столбцы:

```sql
alter table public.profiles
  add column if not exists cheat_local_snapshot jsonb null;
alter table public.profiles
  add column if not exists legit_cloud_snapshot jsonb null;
alter table public.profiles
  add column if not exists is_admin boolean not null default false;
```

Чтобы скрыть аккаунт из топа (например свой админский), в Table Editor или SQL:

```sql
update public.profiles set is_admin = true where fio_key = 'ваш нормализованный fio_key';
```

У **новых** строк без миграции колонки вставка из приложения может вернуть ошибку — сначала выполните `add column ... is_admin` выше.

Опционально — человекочитаемый синоним в SQL (не обязателен для приложения):

```sql
-- Псевдоним в запросах: total_twos AS total_fives
-- Приложение по-прежнему читает/пишет total_fives.
```

## 3. Политики RLS (минимум для проверки)

Пока нет полноценной авторизации пользователей, для **локальной разработки** можно разрешить всё для анонима (не выкладывайте так в открытый доступ с ценными данными):

```sql
create policy "inferno_dev_all" on public.profiles
  for all using (true) with check (true);
```

Позже замените на политики вида «читать все для лидерборда», «писать только свою строку» через Supabase Auth или отдельный серверный ключ.

## 4. Ручное добавление преподавателя

Пример:

```sql
insert into public.profiles (fio, fio_key, nickname, gold, keys, total_fives, title)
values (
  'Иванов Иван Иванович',
  lower(regexp_replace(trim('Иванов Иван Иванович'), '\s+', ' ', 'g')),
  'ИвановИ',
  0, 0, 0, 'Новичок-диктатор'
);
```

Поле `fio_key` должно совпадать с нормализацией в коде: строка в нижнем регистре, один пробел между словами (как делает `login_sync.normalize_fio_key`).

## 5. Первая синхронизация «Аферов Андрей Алексеевич»

Если такого `fio_key` ещё нет в таблице, приложение **само создаст** строку при первом входе с этим ФИО, подставив локальные `total_fives`, `gold`, `keys` и титул из ранга. Остальных преподавателей добавляйте вручную SQL или через Table Editor.

## 6. Переменные окружения в Windows

В PowerShell перед запуском:

```powershell
$env:INFERNO_SUPABASE_URL = "https://xxxx.supabase.co"
$env:INFERNO_SUPABASE_KEY = "eyJhbGciOi..."
py -3 main.py
```

Или задайте системные переменные: **Параметры → Система → О программе → Доп. параметры → Переменные среды**.

## 7. Зависимость Python

```bash
pip install supabase
```

(уже добавлено в `requirements.txt`.)
