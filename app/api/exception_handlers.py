from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.exceptions import ModelListError, SettingsValidationError
from app.services.job_paste_parser import JobPasteParseError
from app.services.llm.base import LLMConfigurationError, LLMError
from app.services.resume_parser import ResumeParseError
from app.services.resume_pdf_export import ResumePdfExportError
from app.services.search.base import SearchError


def _detail(exc: Exception) -> str:
    return str(exc)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(SettingsValidationError)
    async def settings_validation_handler(_request: Request, exc: SettingsValidationError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": _detail(exc)},
        )

    @app.exception_handler(ModelListError)
    async def model_list_handler(_request: Request, exc: ModelListError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(ResumeParseError)
    async def resume_parse_handler(_request: Request, exc: ResumeParseError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": _detail(exc)},
        )

    @app.exception_handler(JobPasteParseError)
    async def job_paste_parse_handler(_request: Request, exc: JobPasteParseError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": _detail(exc)},
        )

    @app.exception_handler(LLMConfigurationError)
    async def llm_configuration_handler(_request: Request, exc: LLMConfigurationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": _detail(exc)},
        )

    @app.exception_handler(LLMError)
    async def llm_error_handler(_request: Request, exc: LLMError):
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"detail": _detail(exc)},
        )

    @app.exception_handler(SearchError)
    async def search_error_handler(_request: Request, exc: SearchError):
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"detail": _detail(exc)},
        )

    @app.exception_handler(ResumePdfExportError)
    async def resume_pdf_export_handler(_request: Request, exc: ResumePdfExportError):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": _detail(exc)},
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(_request: Request, exc: ValueError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": _detail(exc)},
        )
