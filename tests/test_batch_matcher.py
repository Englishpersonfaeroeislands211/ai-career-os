from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models import Job, MatchAnalysis
from app.services.batch_matcher import queue_batch_match_analyses


def _mock_scalars_result(values):
    result = MagicMock()
    result.scalars.return_value.all.return_value = values
    return result


@pytest.mark.asyncio
async def test_queue_batch_queues_all_jobs_when_none_analyzed():
    profile_id = uuid4()
    job_a = Job(id=uuid4(), title="A", company="Co", description="Role A")
    job_b = Job(id=uuid4(), title="B", company="Co", description="Role B")
    db = AsyncMock()
    db.execute = AsyncMock(
        side_effect=[
            _mock_scalars_result([job_a, job_b]),
            _mock_scalars_result([]),
        ]
    )

    queued, skipped = await queue_batch_match_analyses(db, profile_id)

    assert len(queued) == 2
    assert skipped == []
    assert db.add.call_count == 2
    assert db.execute.await_count == 2
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_queue_batch_skips_completed_and_pending():
    profile_id = uuid4()
    job_a = Job(id=uuid4(), title="A", company="Co", description="Role A")
    job_b = Job(id=uuid4(), title="B", company="Co", description="Role B")
    completed = MatchAnalysis(
        id=uuid4(),
        profile_id=profile_id,
        job_id=job_a.id,
        status="completed",
    )
    pending = MatchAnalysis(
        id=uuid4(),
        profile_id=profile_id,
        job_id=job_b.id,
        status="pending",
    )
    db = AsyncMock()
    db.execute = AsyncMock(
        side_effect=[
            _mock_scalars_result([job_a, job_b]),
            _mock_scalars_result([completed, pending]),
        ]
    )

    queued, skipped = await queue_batch_match_analyses(db, profile_id, skip_existing=True)

    assert queued == []
    assert skipped == [job_a.id, job_b.id]
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_queue_batch_reanalyzes_when_skip_existing_false():
    profile_id = uuid4()
    job = Job(id=uuid4(), title="A", company="Co", description="Role A")
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[_mock_scalars_result([job])])

    queued, skipped = await queue_batch_match_analyses(
        db,
        profile_id,
        skip_existing=False,
    )

    assert len(queued) == 1
    assert skipped == []
    db.add.assert_called_once()
    assert db.execute.await_count == 1
