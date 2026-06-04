-- Empresas / contratistas del portal HSEC (campo "Empresa" del scraper de personas)
-- Catálogo por tenant; las personas se vinculan por company_id.

CREATE TABLE IF NOT EXISTS public.companies (
  id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  tenant_id  UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  name       TEXT        NOT NULL,
  is_active  BOOLEAN     NOT NULL DEFAULT true
);

CREATE UNIQUE INDEX companies_tenant_name_unique
  ON public.companies (tenant_id, name);

CREATE INDEX companies_tenant_id_idx
  ON public.companies (tenant_id);

CREATE TRIGGER companies_set_updated_at
  BEFORE UPDATE ON public.companies
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Vincular personas existentes
ALTER TABLE public.hsec_people
  ADD COLUMN IF NOT EXISTS company_id UUID REFERENCES public.companies(id) ON DELETE SET NULL;

CREATE INDEX hsec_people_company_id_idx
  ON public.hsec_people (company_id);

-- Mantener texto crudo del portal para auditoría / comparación en sync
COMMENT ON COLUMN public.hsec_people.empresa IS
  'Nombre de empresa tal como viene del scraper HSEC; company_id es la referencia normalizada.';

-- Backfill: crear empresas desde valores ya scrapeados y enlazar
INSERT INTO public.companies (tenant_id, name)
SELECT DISTINCT hp.tenant_id, trim(hp.empresa)
FROM public.hsec_people hp
WHERE hp.empresa IS NOT NULL
  AND trim(hp.empresa) <> ''
ON CONFLICT (tenant_id, name) DO NOTHING;

UPDATE public.hsec_people hp
SET company_id = c.id
FROM public.companies c
WHERE c.tenant_id = hp.tenant_id
  AND hp.empresa IS NOT NULL
  AND trim(hp.empresa) <> ''
  AND c.name = trim(hp.empresa);

-- Upsert usado por scripts de scraping (service_role)
CREATE OR REPLACE FUNCTION public.upsert_company_for_tenant(
  p_tenant_id UUID,
  p_name TEXT
)
RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_name TEXT := trim(p_name);
  v_id   UUID;
BEGIN
  IF v_name IS NULL OR v_name = '' THEN
    RETURN NULL;
  END IF;

  INSERT INTO public.companies (tenant_id, name)
  VALUES (p_tenant_id, v_name)
  ON CONFLICT (tenant_id, name)
  DO UPDATE SET updated_at = now(), is_active = true
  RETURNING id INTO v_id;

  RETURN v_id;
END;
$$;

REVOKE ALL ON FUNCTION public.upsert_company_for_tenant(UUID, TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.upsert_company_for_tenant(UUID, TEXT) TO service_role;
