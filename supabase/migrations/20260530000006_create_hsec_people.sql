-- Personas extraídas del portal HSEC (ReportePersonalCapacitado)
-- Campos alineados con PersonaScrapedResult en .agents/context/people_scraper.py

CREATE TABLE IF NOT EXISTS public.hsec_people (
  id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_synced_at  TIMESTAMPTZ,
  tenant_id       UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  tipo_documento  TEXT        NOT NULL,
  nro_documento   TEXT        NOT NULL,
  nombres         TEXT        NOT NULL,
  apellidos       TEXT        NOT NULL,
  empresa         TEXT
);

CREATE UNIQUE INDEX hsec_people_tenant_document_unique
  ON public.hsec_people (tenant_id, nro_documento);

CREATE INDEX hsec_people_tenant_id_idx
  ON public.hsec_people (tenant_id);

CREATE INDEX hsec_people_tenant_empresa_idx
  ON public.hsec_people (tenant_id, empresa);

CREATE TRIGGER hsec_people_set_updated_at
  BEFORE UPDATE ON public.hsec_people
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
