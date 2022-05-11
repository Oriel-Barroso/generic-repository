import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = [
    pytest.mark.anyio(),
]


async def test_connection(db_session: AsyncSession):
    result = await db_session.scalar(sa.select(sa.text("2+3")))
    assert result == 5
