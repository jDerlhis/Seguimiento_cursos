-- Corrige linter 0028/0029: RPC público SECURITY DEFINER callable por anon/authenticated.
-- Sustituido por RLS: el usuario autenticado solo puede unirse a sí mismo como member
-- en el tenant pyflow-desktop (sin elevar privilegios vía PostgREST).

DROP FUNCTION IF EXISTS public.ensure_pyflow_desktop_member();

-- Lookup del tenant antes de tener membresía (tenants_select_member exige ser miembro).
DROP POLICY IF EXISTS tenants_select_pyflow_desktop_onboarding ON public.tenants;
CREATE POLICY tenants_select_pyflow_desktop_onboarding
  ON public.tenants
  FOR SELECT
  TO authenticated
  USING (slug = 'pyflow-desktop');

DROP POLICY IF EXISTS tenant_members_insert_self_pyflow_desktop ON public.tenant_members;
CREATE POLICY tenant_members_insert_self_pyflow_desktop
  ON public.tenant_members
  FOR INSERT
  TO authenticated
  WITH CHECK (
    user_id = (SELECT auth.uid())
    AND role = 'member'::public.tenant_member_role
    AND tenant_id IN (
      SELECT id FROM public.tenants WHERE slug = 'pyflow-desktop'
    )
  );
