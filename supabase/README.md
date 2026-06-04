# Backend Supabase (Omnimina)

Proyecto remoto: **omnimina** (`ixwxeebcpvuwtxqqrdjt`)

Todos los comandos se ejecutan desde la **raíz del repo** o desde `backend/`:

```bash
# Desde la raíz (recomendado)
pnpm supabase:projects

# O desde backend/
cd backend && pnpm supabase:projects
```

## CLI conectado

| Paso | Comando | Estado |
|------|---------|--------|
| Login | `pnpm supabase:login` | Sesión activa |
| Link | `pnpm supabase:link` | Vinculado a `ixwxeebcpvuwtxqqrdjt` |
| Verificar | `pnpm supabase:projects` | Debe mostrar ● en omnimina |

## Comandos frecuentes

```bash
pnpm supabase:projects      # proyectos y cuál está linked
pnpm supabase:migrations    # migraciones local vs remoto
pnpm supabase:push          # aplicar migraciones al remoto
pnpm supabase:pull          # traer schema del remoto
pnpm supabase:functions:serve   # edge functions local (requiere Docker)
pnpm supabase:functions:deploy  # desplegar omniback
```

## Desarrollo local (opcional)

Requiere **Docker Desktop** en ejecución:

```bash
pnpm supabase:start
pnpm supabase:status
```

## Primera vez / otro equipo

1. Instalar CLI: `pnpm dlx supabase --version` (o `npm i -g supabase`)
2. Login: `pnpm supabase:login` (abre el navegador)
3. Link: `pnpm supabase:link` (pide la contraseña de Postgres del dashboard)
4. Push: `pnpm supabase:push` (sube las migraciones de `supabase/migrations/`)

Contraseña de DB: [Dashboard → Project Settings → Database](https://supabase.com/dashboard/project/ixwxeebcpvuwtxqqrdjt/settings/database)

## Secrets (Edge Functions)

```bash
pnpm supabase secrets set HSEC_DASHBOARD_URL=https://antapaccay.sam.glencore.net/hsec_web
pnpm supabase secrets list
```

Requiere token de Management API (no basta con `link`).

### Windows: login OK pero `secrets set` falla

En Cursor/VS Code a veces el token no se persiste bien. Workaround con **Personal Access Token**:

1. Crear token en [Account → Access Tokens](https://supabase.com/dashboard/account/tokens) (formato `sbp_...`, no `sbp_v0_...`).
2. En **PowerShell externo** (no integrado de Cursor):

```powershell
cd backend
pnpm exec supabase login --token "sbp_TU_TOKEN"
pnpm supabase secrets set HSEC_DASHBOARD_URL=https://antapaccay.sam.glencore.net/hsec_web
```

O variable de entorno (sesión actual):

```powershell
$env:SUPABASE_ACCESS_TOKEN = "sbp_TU_TOKEN"
pnpm supabase secrets set HSEC_DASHBOARD_URL=https://antapaccay.sam.glencore.net/hsec_web
```

Permanente (nueva terminal después):

```powershell
setx SUPABASE_ACCESS_TOKEN "sbp_TU_TOKEN"
```

> **Nota:** `secrets set` inyecta env vars en **Edge Functions**. El script Deno `hsec_login.ts` usa `.env` local (`HSEC_DASHBOARD_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`).

## Estructura

```
backend/
├── package.json
├── scripts/           # scripts Deno/Node
└── supabase/
    ├── config.toml
    ├── migrations/
    └── functions/omniback/
```

## Modelo de datos (scrapers HSEC)

| Tabla | Origen | Descripción |
|-------|--------|-------------|
| `tenants` | App | Organización (multi-tenant), `slug` para rutas `/t/:slug` |
| `tenant_members` | Auth | Usuario ↔ tenant + rol |
| `hsec_credentials` | Backend | Usuario/password portal HSEC (Vault) — **solo service_role** |
| `hsec_sessions` | Backend | Cookies Playwright — **solo service_role** |
| `hsec_people` | `people_scraper.py` | Personas por DNI |
| `companies` | Campo `empresa` del scraper | Empresas/contratistas por tenant |
| `hsec_courses` | `cursos_scraper.py` | Capacitaciones por persona |

### Empresas (`companies`)

- Una fila por nombre de empresa **dentro del tenant** (único `tenant_id + name`).
- `hsec_people.company_id` → FK opcional a `companies`.
- `hsec_people.empresa` conserva el texto crudo del portal (útil al re-scrapear).
- Función `upsert_company_for_tenant(tenant_id, name)` para scripts con `service_role`.

```sql
-- Registrar empresa manualmente
INSERT INTO public.companies (tenant_id, name)
SELECT id, 'CONTRATISTA XYZ S.A.C.'
FROM public.tenants WHERE slug = 'demo';

-- Vincular persona a empresa
UPDATE public.hsec_people
SET company_id = (
  SELECT c.id FROM public.companies c
  JOIN public.tenants t ON t.id = c.tenant_id
  WHERE t.slug = 'demo' AND c.name = 'CONTRATISTA XYZ S.A.C.'
)
WHERE nro_documento = '12345678';
```

Desde el scraper (service_role):

```sql
SELECT public.upsert_company_for_tenant(
  '<tenant-uuid>',
  'CONTRATISTA XYZ S.A.C.'
);
-- → UUID de companies; usarlo como company_id al insertar/actualizar hsec_people
```

### Roles (`tenant_member_role`)

| Rol | Lectura | Escritura people/courses | Gestionar miembros |
|-----|---------|---------------------------|-------------------|
| `owner` | Sí | Sí | Sí |
| `admin` | Sí | Sí | Sí |
| `member` | Sí | Sí | No |
| `viewer` | Sí | No | No |

### RLS (modelo en dos capas)

Las migraciones **001–003** solo hacían `REVOKE ALL` (quitar permisos directos). La **008** activa RLS y define políticas. Sin la 008, `REVOKE` no equivale a RLS: un `GRANT` accidental dejaría la tabla abierta.

| Tabla | 001–003 | 008 | Quién accede vía API |
|-------|---------|-----|----------------------|
| `tenants` | REVOKE | RLS + `tenants_select_member` + GRANT SELECT | `authenticated` miembro del tenant |
| `hsec_credentials` | REVOKE | RLS ON, **sin políticas** | Solo `service_role` (scripts) |
| `hsec_sessions` | REVOKE | RLS ON, **sin políticas** | Solo `service_role` (scripts) |
| `tenant_members` | — | RLS + políticas por rol | Miembros del tenant |
| `hsec_people` / `hsec_courses` | — | RLS + políticas por rol | Miembros según rol |

`hsec_credentials` / `hsec_sessions` **no están “sin RLS”**: tienen RLS activo a propósito **sin políticas** = deny por defecto para el front (defensa en profundidad junto al REVOKE).

### Seed inicial (SQL Editor)

```sql
-- 1. Tenant con slug para el front
INSERT INTO public.tenants (name, slug)
VALUES ('Antapaccay', 'demo')
ON CONFLICT DO NOTHING;

-- 2. Vincular tu usuario de Supabase Auth como owner
-- (reemplaza USER_UUID por auth.users.id del dashboard Authentication)
INSERT INTO public.tenant_members (tenant_id, user_id, role)
SELECT t.id, 'USER_UUID'::uuid, 'owner'
FROM public.tenants t
WHERE t.slug = 'demo';
```
