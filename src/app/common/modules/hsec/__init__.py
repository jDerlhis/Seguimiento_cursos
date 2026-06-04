"""
Librería de negocio HSEC (port de backend/scripts).

Uso:
    from app.common.modules.hsec import login_hsec, sync_hsec, scrape_person_by_dni
"""

from app.common.modules.hsec.courses_scraper import scrape_courses_by_dni
from app.common.modules.hsec.login import login_hsec
from app.common.modules.hsec.people_scraper import scrape_person_by_dni
from app.common.modules.hsec.sync import sync_hsec
from app.common.modules.hsec.types import (
    HsecCredential,
    LoginResult,
    ScrapedCourse,
    ScrapedPerson,
    StorageState,
    SyncResult,
)

__all__ = [
    "HsecCredential",
    "LoginResult",
    "ScrapedCourse",
    "ScrapedPerson",
    "StorageState",
    "SyncResult",
    "login_hsec",
    "scrape_courses_by_dni",
    "scrape_person_by_dni",
    "sync_hsec",
]
