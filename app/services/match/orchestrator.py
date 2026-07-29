from uuid import UUID

from app.db.session import async_session
from app.logging_config import get_logger
from app.models import Job, MatchAnalysis, Profile
from app.services.llm.base import LLMConfigurationError, LLMError
from app.services.match.analyzer import analyze_match, analyze_matches_screen
from app.services.match.result import full_result_payload, screen_result_payload

logger = get_logger(__name__)


async def run_match_analysis(analysis_id: UUID) -> None:
    """Full-depth match only (manual re-analyze)."""
    await _run_full_match_analysis(analysis_id)


async def _run_full_match_analysis(analysis_id: UUID) -> None:
    async with async_session() as db:
        analysis = await db.get(MatchAnalysis, analysis_id)
        if not analysis:
            return

        profile = await db.get(Profile, analysis.profile_id)
        job = await db.get(Job, analysis.job_id)
        if not profile or not job:
            if analysis.status == "pending":
                analysis.status = "failed"
                analysis.error = "Profile or job not found"
                await db.commit()
            return

        had_screen = isinstance(analysis.result, dict) and analysis.result.get("depth") == "screen"

        try:
            result = await analyze_match(db, profile, job)
            analysis.status = "completed"
            analysis.result = full_result_payload(result)
            analysis.error = None
            logger.info(
                "Match analysis completed: id=%s score=%.1f recommendation=%s",
                analysis_id,
                result.score,
                result.recommendation,
            )
        except (LLMConfigurationError, LLMError) as exc:
            if had_screen:
                analysis.status = "completed"
                analysis.error = f"Deep analysis failed: {exc}"
                logger.warning(
                    "Deep match failed for %s, keeping screen result: %s",
                    analysis_id,
                    exc,
                )
            else:
                analysis.status = "failed"
                analysis.error = str(exc)
                logger.warning("Match analysis failed for %s: %s", analysis_id, exc)
        except Exception as exc:
            if had_screen:
                analysis.status = "completed"
                analysis.error = f"Deep analysis failed: {exc}"
                logger.exception("Unexpected deep match failure for %s", analysis_id)
            else:
                analysis.status = "failed"
                analysis.error = str(exc)
                logger.exception("Unexpected match analysis failure for %s", analysis_id)

        await db.commit()


async def run_progressive_match_analysis(analysis_id: UUID) -> None:
    """Fast screen result first, then replace with full analysis."""
    async with async_session() as db:
        analysis = await db.get(MatchAnalysis, analysis_id)
        if not analysis or analysis.status != "pending":
            return

        profile = await db.get(Profile, analysis.profile_id)
        job = await db.get(Job, analysis.job_id)
        if not profile or not job:
            analysis.status = "failed"
            analysis.error = "Profile or job not found"
            await db.commit()
            return

        try:
            screen_batch = await analyze_matches_screen(db, profile, [job])
            screen_match = next(
                (m for m in screen_batch.matches if m.job_id == job.id),
                None,
            )
            if not screen_match:
                analysis.status = "failed"
                analysis.error = "Screen response missing job_id"
                await db.commit()
                return

            analysis.result = screen_result_payload(screen_match)
            analysis.error = None
            await db.commit()
            logger.info(
                "Screen match completed: id=%s score=%.1f (full analysis queued)",
                analysis_id,
                screen_match.score,
            )
        except (LLMConfigurationError, LLMError) as exc:
            analysis.status = "failed"
            analysis.error = str(exc)
            await db.commit()
            return
        except Exception as exc:
            analysis.status = "failed"
            analysis.error = str(exc)
            logger.exception("Unexpected screen match failure for %s", analysis_id)
            await db.commit()
            return

    await _run_full_match_analysis(analysis_id)
