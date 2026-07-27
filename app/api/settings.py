from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.settings import SettingsRead, SettingsUpdate
from app.services.settings_service import get_settings_read, upsert_settings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsRead)
async def read_settings(db: AsyncSession = Depends(get_db)):
    return await get_settings_read(db)


@router.put("", response_model=SettingsRead)
async def update_settings(body: SettingsUpdate, db: AsyncSession = Depends(get_db)):
    return await upsert_settings(db, body)
