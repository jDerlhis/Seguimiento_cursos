CREATE EXTENSION IF NOT EXISTS supabase_vault CASCADE;

CREATE TABLE IF NOT EXISTS public.hsec_credentials (
  id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  tenant_id       UUID        NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  username        TEXT        NOT NULL,
  vault_secret_id UUID        NOT NULL,
  is_active       BOOLEAN     NOT NULL DEFAULT true
);

-- Una sola credencial activa por tenant
CREATE UNIQUE INDEX hsec_credentials_one_active_per_tenant
  ON public.hsec_credentials (tenant_id)
  WHERE is_active = true;

CREATE TRIGGER hsec_credentials_set_updated_at
  BEFORE UPDATE ON public.hsec_credentials
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

ALTER TABLE public.hsec_credentials ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.hsec_credentials FROM anon, authenticated;

-- ─────────────────────────────────────────────
-- Cómo insertar credenciales:
--
--   1. Crear el secreto en Vault:
--      SELECT vault.create_secret('mi_password', 'descripcion_opcional');
--      → retorna UUID (vault_secret_id)
--
--   2. Insertar credencial:
--      INSERT INTO public.hsec_credentials (tenant_id, username, vault_secret_id)
--      VALUES ('<tenant-uuid>', 'usuario_hsec', '<vault-secret-uuid>');
--
--   3. Leer password descifrado:
--      SELECT decrypted_secret FROM vault.decrypted_secrets WHERE id = '<vault-secret-uuid>';
-- ─────────────────────────────────────────────
