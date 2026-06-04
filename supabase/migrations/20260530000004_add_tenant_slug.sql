ALTER TABLE public.tenants
  ADD COLUMN IF NOT EXISTS slug TEXT;

UPDATE public.tenants
SET slug = lower(regexp_replace(trim(name), '[^a-zA-Z0-9]+', '-', 'g'))
WHERE slug IS NULL;

ALTER TABLE public.tenants
  ALTER COLUMN slug SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS tenants_slug_unique
  ON public.tenants (slug);
