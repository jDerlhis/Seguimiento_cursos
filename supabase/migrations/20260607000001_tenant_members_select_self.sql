-- Onboarding: el usuario autenticado puede leer sus propias filas en tenant_members
-- (necesario antes de ser "miembro" según tenant_member_can_read).

DROP POLICY IF EXISTS tenant_members_select_self ON public.tenant_members;
CREATE POLICY tenant_members_select_self
  ON public.tenant_members
  FOR SELECT
  TO authenticated
  USING (user_id = (SELECT auth.uid()));
