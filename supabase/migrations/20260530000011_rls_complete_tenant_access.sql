-- Aplica en remoto lo que faltaba tras 008 antigua (tenants UPDATE, credentials, sessions).

GRANT SELECT, UPDATE ON public.tenants TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.hsec_credentials TO authenticated;
GRANT SELECT, DELETE ON public.hsec_sessions TO authenticated;

DROP POLICY IF EXISTS tenants_update_writer ON public.tenants;
CREATE POLICY tenants_update_writer
  ON public.tenants
  FOR UPDATE
  TO authenticated
  USING (public.tenant_member_can_write(id))
  WITH CHECK (public.tenant_member_can_write(id));

DROP POLICY IF EXISTS hsec_credentials_select_admin ON public.hsec_credentials;
DROP POLICY IF EXISTS hsec_credentials_insert_admin ON public.hsec_credentials;
DROP POLICY IF EXISTS hsec_credentials_update_admin ON public.hsec_credentials;
DROP POLICY IF EXISTS hsec_credentials_delete_admin ON public.hsec_credentials;

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

DROP POLICY IF EXISTS hsec_sessions_select_admin ON public.hsec_sessions;
DROP POLICY IF EXISTS hsec_sessions_delete_admin ON public.hsec_sessions;

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
