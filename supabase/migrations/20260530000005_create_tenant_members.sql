CREATE TYPE public.tenant_member_role AS ENUM (
  'owner',
  'admin',
  'member',
  'viewer'
);

CREATE TABLE IF NOT EXISTS public.tenant_members (
  id         UUID                   PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMPTZ            NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ            NOT NULL DEFAULT now(),
  tenant_id  UUID                   NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  user_id    UUID                   NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role       public.tenant_member_role NOT NULL DEFAULT 'member'
);

CREATE UNIQUE INDEX tenant_members_tenant_user_unique
  ON public.tenant_members (tenant_id, user_id);

CREATE INDEX tenant_members_user_id_idx
  ON public.tenant_members (user_id);

CREATE TRIGGER tenant_members_set_updated_at
  BEFORE UPDATE ON public.tenant_members
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Una sola membresía owner por tenant (opcional, evita múltiples owners)
CREATE UNIQUE INDEX tenant_members_one_owner_per_tenant
  ON public.tenant_members (tenant_id)
  WHERE role = 'owner';
