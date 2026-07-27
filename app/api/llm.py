from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.llm import ListModelsRequest, ModelListRead
from app.services.llm.model_list import list_provider_models

router = APIRouter(prefix="/llm", tags=["llm"])


@router.post("/models", response_model=ModelListRead)
async def list_models(body: ListModelsRequest, db: AsyncSession = Depends(get_db)):
    models = await list_provider_models(
        db,
        body.llm_provider,
        body.llm_api_key,
        body.llm_base_url,
        body.use_saved_credentials,
    )
    return ModelListRead(models=models)
