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

    print(data_short.Itemlist[0])
    # print(data_long[0])

    assert len(data_short) > 0
    assert len(data_long) > 0


@pytest.mark.asyncio
async def test_ItemCollection():
    search = subitopy.Search()
    item1 = "Iphone 14"
    item2 = "Iphone 14 pro"
    data_1 = await search.search(itemname=item1)
    data_2 = await search.search(itemname=item2)

    print((data_1 + data_2).stats())

    assert len(data_1 + data_2) > 100


@pytest.mark.asyncio
async def test_Advertiser_reviews():

    adv = subitopy.utils.Advertiser(user_id=1823198, is_company=False)
    revs = await adv.reviews()

    assert len(revs) > 1
