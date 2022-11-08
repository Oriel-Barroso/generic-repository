# pylint: disable=import-error,missing-function-docstring
"""Tests for the cached repository.
"""
from unittest import mock

import pytest

from generic_repository import CacheRepository, Repository


@pytest.mark.anyio()
async def test_cached_id():
    mocked_repo = mock.Mock(Repository)
    cached = CacheRepository(mocked_repo)
    await cached.get_by_id(3)
    mocked_repo.get_by_id.assert_called_with(3)
    await cached.get_by_id(3)
    assert mocked_repo.get_by_id.call_count == 1


@pytest.mark.anyio()
async def test_cached_count():
    mocked_repo = mock.Mock(Repository)
    cached = CacheRepository(mocked_repo)
    await cached.get_count(x=3)
    mocked_repo.get_count.assert_called_with(x=3)
    await cached.get_count(x=3)
    assert mocked_repo.get_count.call_count == 1


@pytest.mark.anyio()
async def test_cached_list():
    mocked_repo = mock.Mock(Repository)
    cached = CacheRepository(mocked_repo)
    await cached.get_list(x=3)
    mocked_repo.get_list.assert_called_with(offset=None, size=None, x=3)
    await cached.get_list(x=3)
    assert mocked_repo.get_list.call_count == 1


@pytest.mark.anyio()
async def test_cached_clear_cache():
    mocked_repo = mock.Mock(Repository)
    cached = CacheRepository(mocked_repo)
    await cached.get_list(x=3)
    mocked_repo.get_list.assert_called_with(offset=None, size=None, x=3)
    cached.clear_cache()
    await cached.get_list(x=3)
    assert mocked_repo.get_list.call_count == 2
