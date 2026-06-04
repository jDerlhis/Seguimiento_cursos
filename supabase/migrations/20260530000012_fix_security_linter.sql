-- Corrige alertas del Database Linter de Supabase:
-- - search_path fijo en set_updated_at
-- - helpers RLS en schema private (no expuesto por PostgREST)
-- - REVOKE explícito de EXECUTE en funciones SECURITY DEFINER restantes en public

-- ── set_updated_at ────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = public
AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

-- ── Schema private (solo uso interno: RLS, triggers, service_role) ───────────

CREATE SCHEMA IF NOT EXISTS private;

REVOKE ALL ON SCHEMA private FROM PUBLIC;
REVOKE ALL ON SCHEMA private FROM anon, authenticated;

GRANT USAGE ON SCHEMA private TO postgres, service_role;

-- ── Helpers RLS (antes en public) ───────────────────────────────────────────

CREATE OR REPLACE FUNCTION private.auth_user_tenant_ids()
RETURNS SETOF UUID
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT tm.tenant_id
  FROM public.tenant_members tm
  WHERE tm.user_id = (SELECT auth.uid());
$$;

CREATE OR REPLACE FUNCTION private.tenant_member_can_read(p_tenant_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1
    FROM public.tenant_members tm
    WHERE tm.user_id = (SELECT auth.uid())
      AND tm.tenant_id = p_tenant_id
      AND tm.role IN ('owner', 'admin', 'member', 'viewer')
  );
$$;

CREATE OR REPLACE FUNCTION private.tenant_member_can_write(p_tenant_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1
    FROM public.tenant_members tm
    WHERE tm.user_id = (SELECT auth.uid())
      AND tm.tenant_id = p_tenant_id
      AND tm.role IN ('owner', 'admin', 'member')
  );
$$;

CREATE OR REPLACE FUNCTION private.tenant_member_is_admin(p_tenant_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1
    FROM public.tenant_members tm
    WHERE tm.user_id = (SELECT auth.uid())
      AND tm.tenant_id = p_tenant_id
      AND tm.role IN ('owner', 'admin')
  );
$$;

REVOKE ALL ON FUNCTION private.auth_user_tenant_ids() FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION private.tenant_member_can_read(UUID) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION private.tenant_member_can_write(UUID) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION private.tenant_member_is_admin(UUID) FROM PUBLIC, anon, authenticated;

GRANT EXECUTE ON FUNCTION private.auth_user_tenant_ids() TO postgres, service_role;
GRANT EXECUTE ON FUNCTION private.tenant_member_can_read(UUID) TO postgres, service_role;
GRANT EXECUTE ON FUNCTION private.tenant_member_can_write(UUID) TO postgres, service_role;
GRANT EXECUTE ON FUNCTION private.tenant_member_is_admin(UUID) TO postgres, service_role;

-- ── Políticas RLS → private.* (antes de DROP en public) ───────────────────────

ALTER POLICY tenants_select_member ON public.tenants
  USING (private.tenant_member_can_read(id));

ALTER POLICY tenants_update_writer ON public.tenants
  USING (private.tenant_member_can_write(id))
  WITH CHECK (private.tenant_member_can_write(id));

ALTER POLICY tenant_members_select_same_tenant ON public.tenant_members
  USING (private.tenant_member_can_read(tenant_id));

ALTER POLICY tenant_members_insert_admin ON public.tenant_members
  WITH CHECK (private.tenant_member_is_admin(tenant_id));

ALTER POLICY tenant_members_update_admin ON public.tenant_members
  USING (private.tenant_member_is_admin(tenant_id))
  WITH CHECK (private.tenant_member_is_admin(tenant_id));

ALTER POLICY tenant_members_delete_admin ON public.tenant_members
  USING (private.tenant_member_is_admin(tenant_id));

ALTER POLICY hsec_credentials_select_admin ON public.hsec_credentials
  USING (private.tenant_member_is_admin(tenant_id));

ALTER POLICY hsec_credentials_insert_admin ON public.hsec_credentials
  WITH CHECK (private.tenant_member_is_admin(tenant_id));

ALTER POLICY hsec_credentials_update_admin ON public.hsec_credentials
  USING (private.tenant_member_is_admin(tenant_id))
  WITH CHECK (private.tenant_member_is_admin(tenant_id));

ALTER POLICY hsec_credentials_delete_admin ON public.hsec_credentials
  USING (private.tenant_member_is_admin(tenant_id));

ALTER POLICY hsec_sessions_select_admin ON public.hsec_sessions
  USING (private.tenant_member_is_admin(tenant_id));

ALTER POLICY hsec_sessions_delete_admin ON public.hsec_sessions
  USING (private.tenant_member_is_admin(tenant_id));

ALTER POLICY hsec_people_select_member ON public.hsec_people
  USING (private.tenant_member_can_read(tenant_id));

ALTER POLICY hsec_people_insert_writer ON public.hsec_people
  WITH CHECK (
    private.tenant_member_can_write(tenant_id)
    AND (
      company_id IS NULL
      OR EXISTS (
        SELECT 1
        FROM public.companies c
        WHERE c.id = company_id
          AND c.tenant_id = hsec_people.tenant_id
      )
    )
  );

ALTER POLICY hsec_people_update_writer ON public.hsec_people
  USING (private.tenant_member_can_write(tenant_id))
  WITH CHECK (
    private.tenant_member_can_write(tenant_id)
    AND (
      company_id IS NULL
      OR EXISTS (
        SELECT 1
        FROM public.companies c
        WHERE c.id = company_id
          AND c.tenant_id = hsec_people.tenant_id
      )
    )
  );

ALTER POLICY hsec_people_delete_admin ON public.hsec_people
  USING (private.tenant_member_is_admin(tenant_id));

ALTER POLICY hsec_courses_select_member ON public.hsec_courses
  USING (private.tenant_member_can_read(tenant_id));

ALTER POLICY hsec_courses_insert_writer ON public.hsec_courses
  WITH CHECK (
    private.tenant_member_can_write(tenant_id)
    AND EXISTS (
      SELECT 1
      FROM public.hsec_people p
      WHERE p.id = person_id
        AND p.tenant_id = hsec_courses.tenant_id
    )
  );

ALTER POLICY hsec_courses_update_writer ON public.hsec_courses
  USING (private.tenant_member_can_write(tenant_id))
  WITH CHECK (
    private.tenant_member_can_write(tenant_id)
    AND EXISTS (
      SELECT 1
      FROM public.hsec_people p
      WHERE p.id = person_id
        AND p.tenant_id = hsec_courses.tenant_id
    )
  );

ALTER POLICY hsec_courses_delete_admin ON public.hsec_courses
  USING (private.tenant_member_is_admin(tenant_id));

ALTER POLICY companies_select_member ON public.companies
  USING (private.tenant_member_can_read(tenant_id));

ALTER POLICY companies_insert_writer ON public.companies
  WITH CHECK (private.tenant_member_can_write(tenant_id));

ALTER POLICY companies_update_writer ON public.companies
  USING (private.tenant_member_can_write(tenant_id))
  WITH CHECK (private.tenant_member_can_write(tenant_id));

ALTER POLICY companies_delete_admin ON public.companies
  USING (private.tenant_member_is_admin(tenant_id));

DROP FUNCTION IF EXISTS public.auth_user_tenant_ids();
DROP FUNCTION IF EXISTS public.tenant_member_can_read(UUID);
DROP FUNCTION IF EXISTS public.tenant_member_can_write(UUID);
DROP FUNCTION IF EXISTS public.tenant_member_is_admin(UUID);

-- ── upsert_company_for_tenant (RPC solo service_role) ───────────────────────

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

REVOKE ALL ON FUNCTION public.upsert_company_for_tenant(UUID, TEXT) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.upsert_company_for_tenant(UUID, TEXT) TO service_role;

-- ── rls_auto_enable (función de plataforma Supabase, si existe) ───────────────

DO $$
BEGIN
  IF to_regprocedure('public.rls_auto_enable()') IS NOT NULL THEN
    REVOKE ALL ON FUNCTION public.rls_auto_enable() FROM PUBLIC, anon, authenticated;
    GRANT EXECUTE ON FUNCTION public.rls_auto_enable() TO postgres, service_role;
  END IF;
END $$;
