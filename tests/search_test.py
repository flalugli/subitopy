import os
import sys
import time

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
async def test_fetch_data_2pages():
    search = subitopy.Search()
    item = "Iphone 14"
    data_short = await search.search(itemname=item, pages=2)
    data_long = await search.search(itemname=item, short=False, pages=2)

    print(len(data_short))
    # print(data_long[0])

    assert len(data_short) > 101
    assert len(data_long) > 101


@pytest.mark.asyncio
async def test_fetch_data_filtered():
    search = subitopy.Search()
    item = "iphone 14"
    data_short = await search.search(itemname=item, pages=5, conditions=[20, 30, 40])

    items = data_short.filter_strings(
        ["rotto", "non funzionante", "danneggiato"],
        search_inname=["cover", "custodia", "pro"],
    )

    print(items.stats())

    assert len(items) > 1


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

    adv = subitopy.classes.Advertiser(user_id=1823198, is_company=False)
    revs = await adv.reviews()

    assert len(revs) > 1


@pytest.mark.asyncio
async def test_cached_search():

    search = subitopy.Search()
    item = "Iphone 14"

    now = time.time()
    data_now = await search.search(itemname=item, pages=5,cached=True)
    after = time.time()
    now2 = time.time()
    data_after = await search.search(itemname=item, pages=5,cached = True)
    after2 = time.time()

    delta_2 = after2 - now2
    delta_1 = after - now

    print(delta_2)
    print(delta_1)

    assert len(data_now.Itemlist) > 1 and len(data_after.Itemlist) > 1
    assert delta_2 < delta_1

