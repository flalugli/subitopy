import os
import sys

# Add the 'src' directory to the sys.path for module discovery
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

import pytest

import subitopy

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
async def test_fetch_data():
    search = subitopy.Search()
    item = "Iphone 14"
    data_short = await search.search(itemname=item)
    data_long = await search.search(itemname=item, short=False)
    assert len(data_short) > 0
    assert len(data_long) > 0
