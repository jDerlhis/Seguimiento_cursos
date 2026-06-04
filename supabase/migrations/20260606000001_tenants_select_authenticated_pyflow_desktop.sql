-- Permite a usuarios autenticados (sin membresía aún) leer el tenant pyflow-desktop.
-- Complementa tenants_pyflow_desktop_select (solo anon) y tenants_select_member.

DROP POLICY IF EXISTS tenants_select_pyflow_desktop_onboarding ON public.tenants;
CREATE POLICY tenants_select_pyflow_desktop_onboarding
  ON public.tenants
  FOR SELECT
  TO authenticated
  USING (slug = 'pyflow-desktop');
