-- Tras registro/login: asigna al usuario al tenant pyflow-desktop (rol member).
-- Supersedido por 20260605000001_fix_ensure_pyflow_desktop_member_linter.sql (RLS, sin RPC público).

CREATE OR REPLACE FUNCTION public.ensure_pyflow_desktop_member()
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_tenant_id UUID;
  v_user_id   UUID := auth.uid();
BEGIN
  IF v_user_id IS NULL THEN
    RETURN FALSE;
  END IF;

  SELECT id INTO v_tenant_id
  FROM public.tenants
  WHERE slug = 'pyflow-desktop'
  LIMIT 1;

  IF v_tenant_id IS NULL THEN
    RETURN FALSE;
  END IF;

  INSERT INTO public.tenant_members (tenant_id, user_id, role)
  VALUES (v_tenant_id, v_user_id, 'member')
  ON CONFLICT (tenant_id, user_id) DO NOTHING;

  RETURN TRUE;
END;
$$;

REVOKE ALL ON FUNCTION public.ensure_pyflow_desktop_member() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.ensure_pyflow_desktop_member() TO authenticated;
