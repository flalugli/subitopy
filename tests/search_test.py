import sys
import os

# Add the 'src' directory to the sys.path for module discovery
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import subitopy  
import asyncio
import pytest

pytest_plugins = ('pytest_asyncio',)

@pytest.mark.asyncio
async def test_fetch_data():
    search=subitopy.Search()
    data= await search.search(itemname="Iphone 14")
    assert len(data) > 0
