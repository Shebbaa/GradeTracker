-- Inferno Grade Tracker: реферальная система «Вербовщик Палачей»
-- Выполни в SQL Editor проекта Supabase (PostgreSQL).

ALTER TABLE profiles ADD COLUMN IF NOT EXISTS referral_code text;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS referred_by uuid REFERENCES profiles(id);

CREATE UNIQUE INDEX IF NOT EXISTS profiles_referral_code_unique
  ON profiles (referral_code)
  WHERE referral_code IS NOT NULL AND referral_code <> '';

COMMENT ON COLUMN profiles.referral_code IS 'Уникальный код вида INFERNO-777 для приглашений';
COMMENT ON COLUMN profiles.referred_by IS 'Кто пригласил (FK на profiles.id)';
