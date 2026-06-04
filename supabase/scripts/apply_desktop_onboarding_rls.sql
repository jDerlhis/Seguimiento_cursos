-- Ejecutar una vez en Supabase → SQL Editor (proyecto remoto).
-- Permite registro/login en Pyflow desktop sin RPC SECURITY DEFINER.

DROP FUNCTION IF EXISTS public.ensure_pyflow_desktop_member();

DROP POLICY IF EXISTS tenants_select_pyflow_desktop_onboarding ON public.tenants;
CREATE POLICY tenants_select_pyflow_desktop_onboarding
  ON public.tenants FOR SELECT TO authenticated
  USING (slug = 'pyflow-desktop');

DROP POLICY IF EXISTS tenant_members_insert_self_pyflow_desktop ON public.tenant_members;
CREATE POLICY tenant_members_insert_self_pyflow_desktop
  ON public.tenant_members FOR INSERT TO authenticated
  WITH CHECK (
    user_id = (SELECT auth.uid())
    AND role = 'member'::public.tenant_member_role
    AND tenant_id IN (SELECT id FROM public.tenants WHERE slug = 'pyflow-desktop')
  );

DROP POLICY IF EXISTS tenant_members_select_self ON public.tenant_members;
CREATE POLICY tenant_members_select_self
  ON public.tenant_members FOR SELECT TO authenticated
  USING (user_id = (SELECT auth.uid()));

-- Helpers RLS (private.*) + acceso HSEC para role member
GRANT EXECUTE ON FUNCTION private.auth_user_tenant_ids() TO authenticated;
GRANT EXECUTE ON FUNCTION private.tenant_member_can_read(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION private.tenant_member_can_write(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION private.tenant_member_is_admin(UUID) TO authenticated;

DROP POLICY IF EXISTS hsec_sessions_select_member ON public.hsec_sessions;
CREATE POLICY hsec_sessions_select_member ON public.hsec_sessions
  FOR SELECT TO authenticated
  USING (private.tenant_member_can_read(tenant_id));

DROP POLICY IF EXISTS hsec_sessions_insert_writer ON public.hsec_sessions;
CREATE POLICY hsec_sessions_insert_writer ON public.hsec_sessions
  FOR INSERT TO authenticated
  WITH CHECK (private.tenant_member_can_write(tenant_id));

DROP POLICY IF EXISTS hsec_sessions_update_writer ON public.hsec_sessions;
CREATE POLICY hsec_sessions_update_writer ON public.hsec_sessions
  FOR UPDATE TO authenticated
  USING (private.tenant_member_can_write(tenant_id))
  WITH CHECK (private.tenant_member_can_write(tenant_id));

GRANT INSERT, UPDATE ON public.hsec_sessions TO authenticated;

DROP POLICY IF EXISTS hsec_credentials_select_member ON public.hsec_credentials;
CREATE POLICY hsec_credentials_select_member ON public.hsec_credentials
  FOR SELECT TO authenticated
  USING (private.tenant_member_can_read(tenant_id));
