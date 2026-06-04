-- Miembros (role member) deben usar HSEC desde la app desktop.
-- Tras 20260530000012, authenticated no tenía EXECUTE en helpers private.* usados por RLS.

GRANT EXECUTE ON FUNCTION private.auth_user_tenant_ids() TO authenticated;
GRANT EXECUTE ON FUNCTION private.tenant_member_can_read(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION private.tenant_member_can_write(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION private.tenant_member_is_admin(UUID) TO authenticated;

-- hsec_sessions: lectura/escritura para miembros del tenant (no solo admin)
DROP POLICY IF EXISTS hsec_sessions_select_member ON public.hsec_sessions;
CREATE POLICY hsec_sessions_select_member
  ON public.hsec_sessions
  FOR SELECT
  TO authenticated
  USING (private.tenant_member_can_read(tenant_id));

DROP POLICY IF EXISTS hsec_sessions_insert_writer ON public.hsec_sessions;
CREATE POLICY hsec_sessions_insert_writer
  ON public.hsec_sessions
  FOR INSERT
  TO authenticated
  WITH CHECK (private.tenant_member_can_write(tenant_id));

DROP POLICY IF EXISTS hsec_sessions_update_writer ON public.hsec_sessions;
CREATE POLICY hsec_sessions_update_writer
  ON public.hsec_sessions
  FOR UPDATE
  TO authenticated
  USING (private.tenant_member_can_write(tenant_id))
  WITH CHECK (private.tenant_member_can_write(tenant_id));

GRANT INSERT, UPDATE ON public.hsec_sessions TO authenticated;

-- hsec_credentials: lectura para miembros (login HSEC desde credenciales del tenant)
DROP POLICY IF EXISTS hsec_credentials_select_member ON public.hsec_credentials;
CREATE POLICY hsec_credentials_select_member
  ON public.hsec_credentials
  FOR SELECT
  TO authenticated
  USING (private.tenant_member_can_read(tenant_id));
