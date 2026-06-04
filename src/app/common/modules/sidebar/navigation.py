from dataclasses import dataclass, field


@dataclass(frozen=True)
class NavItem:
    key: str
    title: str
    icon: str | None = None


@dataclass(frozen=True)
class NavMenu:
    title: str
    icon: str | None = None
    subtitle: str | None = None
    items: list[NavItem] = field(default_factory=list)


@dataclass(frozen=True)
class NavSection:
    id: str
    label: str
    icon: str
    selected_icon: str
    menus: list[NavMenu] = field(default_factory=list)


NAV_SECTIONS: list[NavSection] = [
    NavSection(
        id="home",
        label="Inicio",
        icon="home_outlined",
        selected_icon="home",
        menus=[
            NavMenu(
                title="Panel",
                icon="dashboard_outlined",
                items=[
                    NavItem("dashboard", "Dashboard", "grid_view"),
                    NavItem("activity", "Actividad reciente", "history"),
                ],
            ),
        ],
    ),
    NavSection(
        id="data",
        label="Datos",
        icon="storage_outlined",
        selected_icon="storage",
        menus=[
            NavMenu(
                title="HSEC",
                icon="language",
                items=[
                    NavItem("hsec", "Conexión", "link"),
                    NavItem("hsec_sync", "Sincronización", "sync"),
                ],
            ),
        ],
    ),
    NavSection(
        id="settings",
        label="Ajustes",
        icon="settings_outlined",
        selected_icon="settings",
        menus=[
            NavMenu(
                title="Aplicación",
                icon="tune",
                items=[
                    NavItem("general", "General", "tune"),
                    NavItem("appearance", "Apariencia", "palette_outlined"),
                ],
            ),
            NavMenu(
                title="Cuenta",
                icon="manage_accounts_outlined",
                items=[
                    NavItem("profile", "Perfil", "person_outlined"),
                    NavItem("security", "Seguridad", "lock_outlined"),
                ],
            ),
        ],
    ),
]

DEFAULT_SECTION_ID = NAV_SECTIONS[0].id
DEFAULT_ITEM_KEY = NAV_SECTIONS[0].menus[0].items[0].key
