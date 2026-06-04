ALTER TABLE public.companies ENABLE ROW LEVEL SECURITY;

GRANT SELECT, INSERT, UPDATE, DELETE ON public.companies TO authenticated;

-- ── companies ─────────────────────────────────────────────────────────────────

CREATE POLICY companies_select_member
  ON public.companies
  FOR SELECT
  TO authenticated
  USING (public.tenant_member_can_read(tenant_id));

CREATE POLICY companies_insert_writer
  ON public.companies
  FOR INSERT
  TO authenticated
  WITH CHECK (public.tenant_member_can_write(tenant_id));

CREATE POLICY companies_update_writer
  ON public.companies
  FOR UPDATE
  TO authenticated
  USING (public.tenant_member_can_write(tenant_id))
  WITH CHECK (public.tenant_member_can_write(tenant_id));

CREATE POLICY companies_delete_admin
  ON public.companies
  FOR DELETE
  TO authenticated
  USING (public.tenant_member_is_admin(tenant_id));

-- Reforzar hsec_people: company_id debe pertenecer al mismo tenant
DROP POLICY IF EXISTS hsec_people_insert_writer ON public.hsec_people;
DROP POLICY IF EXISTS hsec_people_update_writer ON public.hsec_people;

CREATE POLICY hsec_people_insert_writer
  ON public.hsec_people
  FOR INSERT
  TO authenticated
  WITH CHECK (
    public.tenant_member_can_write(tenant_id)
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

CREATE POLICY hsec_people_update_writer
  ON public.hsec_people
  FOR UPDATE
  TO authenticated
  USING (public.tenant_member_can_write(tenant_id))
  WITH CHECK (
    public.tenant_member_can_write(tenant_id)
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
