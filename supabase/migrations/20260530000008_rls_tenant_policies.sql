-- ─────────────────────────────────────────────────────────────────────────────
-- Helpers RLS (SECURITY DEFINER) — membership en app_metadata / tenant_members
-- Usar (select auth.uid()) para rendimiento en políticas.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.auth_user_tenant_ids()
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

CREATE OR REPLACE FUNCTION public.tenant_member_can_read(p_tenant_id UUID)
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

CREATE OR REPLACE FUNCTION public.tenant_member_can_write(p_tenant_id UUID)
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

CREATE OR REPLACE FUNCTION public.tenant_member_is_admin(p_tenant_id UUID)
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

REVOKE ALL ON FUNCTION public.auth_user_tenant_ids() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.tenant_member_can_read(UUID) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.tenant_member_can_write(UUID) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.tenant_member_is_admin(UUID) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION public.auth_user_tenant_ids() TO authenticated;
GRANT EXECUTE ON FUNCTION public.tenant_member_can_read(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION public.tenant_member_can_write(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION public.tenant_member_is_admin(UUID) TO authenticated;

ALTER TABLE public.tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tenant_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.hsec_people ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.hsec_courses ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.hsec_credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.hsec_sessions ENABLE ROW LEVEL SECURITY;

GRANT SELECT, UPDATE ON public.tenants TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.tenant_members TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.hsec_people TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.hsec_courses TO authenticated;

CREATE POLICY tenants_select_member
  ON public.tenants
  FOR SELECT
  TO authenticated
  USING (public.tenant_member_can_read(id));

CREATE POLICY tenants_update_writer
  ON public.tenants
  FOR UPDATE
  TO authenticated
  USING (public.tenant_member_can_write(id))
  WITH CHECK (public.tenant_member_can_write(id));

CREATE POLICY tenant_members_select_same_tenant
  ON public.tenant_members
  FOR SELECT
  TO authenticated
  USING (public.tenant_member_can_read(tenant_id));

CREATE POLICY tenant_members_insert_admin
  ON public.tenant_members
  FOR INSERT
  TO authenticated
  WITH CHECK (public.tenant_member_is_admin(tenant_id));

CREATE POLICY tenant_members_update_admin
  ON public.tenant_members
  FOR UPDATE
  TO authenticated
  USING (public.tenant_member_is_admin(tenant_id))
  WITH CHECK (public.tenant_member_is_admin(tenant_id));

CREATE POLICY tenant_members_delete_admin
  ON public.tenant_members
  FOR DELETE
  TO authenticated
  USING (public.tenant_member_is_admin(tenant_id));

CREATE POLICY hsec_credentials_select_admin
  ON public.hsec_credentials
  FOR SELECT
  TO authenticated
  USING (public.tenant_member_is_admin(tenant_id));

CREATE POLICY hsec_credentials_insert_admin
  ON public.hsec_credentials
  FOR INSERT
  TO authenticated
  WITH CHECK (public.tenant_member_is_admin(tenant_id));

CREATE POLICY hsec_credentials_update_admin
  ON public.hsec_credentials
  FOR UPDATE
  TO authenticated
  USING (public.tenant_member_is_admin(tenant_id))
  WITH CHECK (public.tenant_member_is_admin(tenant_id));

CREATE POLICY hsec_credentials_delete_admin
  ON public.hsec_credentials
  FOR DELETE
  TO authenticated
  USING (public.tenant_member_is_admin(tenant_id));

CREATE POLICY hsec_sessions_select_admin
  ON public.hsec_sessions
  FOR SELECT
  TO authenticated
  USING (public.tenant_member_is_admin(tenant_id));

CREATE POLICY hsec_sessions_delete_admin
  ON public.hsec_sessions
  FOR DELETE
  TO authenticated
  USING (public.tenant_member_is_admin(tenant_id));

GRANT SELECT, INSERT, UPDATE, DELETE ON public.hsec_credentials TO authenticated;
GRANT SELECT, DELETE ON public.hsec_sessions TO authenticated;

CREATE POLICY hsec_people_select_member
  ON public.hsec_people
  FOR SELECT
  TO authenticated
  USING (public.tenant_member_can_read(tenant_id));

CREATE POLICY hsec_people_insert_writer
  ON public.hsec_people
  FOR INSERT
  TO authenticated
  WITH CHECK (public.tenant_member_can_write(tenant_id));

CREATE POLICY hsec_people_update_writer
  ON public.hsec_people
  FOR UPDATE
  TO authenticated
  USING (public.tenant_member_can_write(tenant_id))
  WITH CHECK (public.tenant_member_can_write(tenant_id));

CREATE POLICY hsec_people_delete_admin
  ON public.hsec_people
  FOR DELETE
  TO authenticated
  USING (public.tenant_member_is_admin(tenant_id));

-- ── hsec_courses ──────────────────────────────────────────────────────────────

CREATE POLICY hsec_courses_select_member
  ON public.hsec_courses
  FOR SELECT
  TO authenticated
  USING (public.tenant_member_can_read(tenant_id));

CREATE POLICY hsec_courses_insert_writer
  ON public.hsec_courses
  FOR INSERT
  TO authenticated
  WITH CHECK (
    public.tenant_member_can_write(tenant_id)
    AND EXISTS (
      SELECT 1
      FROM public.hsec_people p
      WHERE p.id = person_id
        AND p.tenant_id = hsec_courses.tenant_id
    )
  );

CREATE POLICY hsec_courses_update_writer
  ON public.hsec_courses
  FOR UPDATE
  TO authenticated
  USING (public.tenant_member_can_write(tenant_id))
  WITH CHECK (
    public.tenant_member_can_write(tenant_id)
    AND EXISTS (
      SELECT 1
      FROM public.hsec_people p
      WHERE p.id = person_id
        AND p.tenant_id = hsec_courses.tenant_id
    )
  );

CREATE POLICY hsec_courses_delete_admin
  ON public.hsec_courses
  FOR DELETE
  TO authenticated
  USING (public.tenant_member_is_admin(tenant_id));
