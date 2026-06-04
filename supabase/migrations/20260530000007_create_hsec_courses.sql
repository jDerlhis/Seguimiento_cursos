-- Capacitaciones extraídas del portal HSEC (tabla "Capacitación Recibida")
-- Campos alineados con CursoScrapedResult en .agents/context/cursos_scraper.py

CREATE TABLE IF NOT EXISTS public.hsec_courses (
  id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_synced_at  TIMESTAMPTZ,
  tenant_id       UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  person_id       UUID        NOT NULL REFERENCES public.hsec_people(id) ON DELETE CASCADE,
  fecha           TEXT,
  duracion        TEXT,
  tema            TEXT        NOT NULL,
  area            TEXT,
  tipo            TEXT,
  nota            TEXT,
  estado          TEXT,
  vencimiento     TEXT
);

-- Evita duplicar el mismo curso en re-scrapes (fecha NULL cuenta como un solo valor)
CREATE UNIQUE INDEX hsec_courses_person_tema_fecha_unique
  ON public.hsec_courses (tenant_id, person_id, tema, fecha)
  NULLS NOT DISTINCT;

CREATE INDEX hsec_courses_tenant_id_idx
  ON public.hsec_courses (tenant_id);

CREATE INDEX hsec_courses_person_id_idx
  ON public.hsec_courses (person_id);

CREATE INDEX hsec_courses_tenant_estado_idx
  ON public.hsec_courses (tenant_id, estado);

CREATE TRIGGER hsec_courses_set_updated_at
  BEFORE UPDATE ON public.hsec_courses
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
