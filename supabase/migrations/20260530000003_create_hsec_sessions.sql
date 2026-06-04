CREATE TABLE IF NOT EXISTS public.hsec_sessions (
  id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  tenant_id        UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  credential_id    UUID        NOT NULL REFERENCES public.hsec_credentials(id) ON DELETE CASCADE,
  storage_state    JSONB       NOT NULL,
  is_active        BOOLEAN     NOT NULL DEFAULT true,
  last_verified_at TIMESTAMPTZ,
  error            TEXT
);

-- Una sola sesión activa por tenant
CREATE UNIQUE INDEX hsec_sessions_one_active_per_tenant
  ON public.hsec_sessions (tenant_id)
  WHERE is_active = true;

CREATE TRIGGER hsec_sessions_set_updated_at
  BEFORE UPDATE ON public.hsec_sessions
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

ALTER TABLE public.hsec_sessions ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.hsec_sessions FROM anon, authenticated;
