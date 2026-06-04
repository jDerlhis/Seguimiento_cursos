-- Pyflow desktop (fase 1): tenant dedicado + políticas RLS para rol anon (publishable key).
-- Alcance limitado al tenant con slug configurable en app (por defecto pyflow-desktop).

INSERT INTO public.tenants (name, slug)
VALUES ('Pyflow Desktop', 'pyflow-desktop')
ON CONFLICT (slug) DO NOTHING;

GRANT SELECT ON public.tenants TO anon;

DROP POLICY IF EXISTS tenants_pyflow_desktop_select ON public.tenants;
CREATE POLICY tenants_pyflow_desktop_select
  ON public.tenants
  FOR SELECT
  TO anon
  USING (slug = 'pyflow-desktop');

DROP POLICY IF EXISTS hsec_people_pyflow_desktop ON public.hsec_people;
DROP POLICY IF EXISTS hsec_courses_pyflow_desktop ON public.hsec_courses;

CREATE POLICY hsec_people_pyflow_desktop
  ON public.hsec_people
  FOR ALL
  TO anon
  USING (
    tenant_id IN (SELECT id FROM public.tenants WHERE slug = 'pyflow-desktop')
  )
  WITH CHECK (
    tenant_id IN (SELECT id FROM public.tenants WHERE slug = 'pyflow-desktop')
  );

CREATE POLICY hsec_courses_pyflow_desktop
  ON public.hsec_courses
  FOR ALL
  TO anon
  USING (
    tenant_id IN (SELECT id FROM public.tenants WHERE slug = 'pyflow-desktop')
  )
  WITH CHECK (
    tenant_id IN (SELECT id FROM public.tenants WHERE slug = 'pyflow-desktop')
  );
