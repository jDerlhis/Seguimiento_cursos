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
