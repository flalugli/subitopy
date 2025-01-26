import asyncio
import math
from itertools import chain

from .errors import MunicipalityError
from .utils import AsyncRequest, QueryParameters


class Search:

    def __init__(
        self,
        base_url: str = "https://www.subito.it",
        api_version: int = 1,
        proxy: str | None = None,
    ) -> None:

        self.api_version = api_version
        self.base_url = base_url

        self.search_api_url = self.base_url + f"/hades/v{api_version}/search/items"
        self.proxy = proxy
        self.request = AsyncRequest(tries=3)

    def bool2query(self, arg: bool) -> str:

        # raise error if this doesnt work
        result = str(arg).lower()

        return result

    async def get_page(self, query: dict, items_only: bool = True):

        page: dict = await self.request.get(
            url=self.search_api_url, params=query, proxy=self.proxy
        )

        if items_only:
            return page["ads"]
        else:
            return page

    async def get_page_short(self, query: dict):
        # get page of items with short info about them

        page = await self.get_page(query)

        page_short = []

        for item in page:
            item_shortinfo = self.get_item_shortinfo(item)
            page_short.append(item_shortinfo)

        return page_short

    async def count_all_items(self, query: dict) -> int:
        page = await self.get_page(query, items_only=False)
        n = page["count_all"]
        return n

    async def search(
        self,
        itemname: str,
        category: int | str = QueryParameters.Categories.EMPTY,
        page_results: int = 100,
        sort_by: int | str = QueryParameters.Sort.DATE,
        ad_type: int | str = QueryParameters.Ad_Type.FOR_SALE,
        region: int | str = QueryParameters.Regions.EMPTY,
        titlesearch_only: bool = True,
        shipping_only: bool = False,
        municipality: str = "",
        pages: int | str = 1,
        startingpage: int = 0,
        short: bool = True,
    ):
        # short is short format with less informations for each item and on by default, pages should never be more than 20, proxy might not work otherwise and you might get ratelimited

        if region == 0:
            # set region to empty string for query
            region = ""
            if len(str(municipality)) > 0:
                raise MunicipalityError(
                    "Please specify the region where the municipality is located"
                )

        all_pages = False

        if isinstance(pages, str):
            if pages.lower() == "all":
                pages = 1
                all_pages = True
            else:
                # log that only one page will be scraped
                pages = 1

        startingpoints: list = []
        endpoints: list = []

        tasks: list = []
        if all_pages:
            query = {
                "q": itemname,
                "c": category,
                "r": region,
                "to": str(municipality),
                "t": ad_type,
                "qso": self.bool2query(titlesearch_only),
                "shp": self.bool2query(shipping_only),
                "sort": sort_by,
                "start": 0,
                "lim": 1,
            }
            total_items = await self.count_all_items(query)
            pages = math.ceil(total_items / page_results)
        for n in range(pages):
            endpoint = (n + 1 + startingpage) * page_results
            startingpoint = endpoint - page_results
            startingpoints.append(startingpoint)
            endpoints.append(endpoint)
            query = {
                "q": itemname,
                "c": category,
                "r": region,
                "to": str(municipality),
                "t": ad_type,
                "qso": self.bool2query(titlesearch_only),
                "shp": self.bool2query(shipping_only),
                "sort": sort_by,
                "start": startingpoint,
                "lim": endpoint,
            }
            if short:
                tasks.append(asyncio.ensure_future(self.get_page_short(query)))
            else:
                tasks.append(asyncio.ensure_future(self.get_page(query)))
        results = await asyncio.gather(*tasks)
        data = list(chain(*results))  # get items from each page all in one array
        return data

    def get_item_shortinfo(self, item: dict):
        # TODO
        # Make typeddict for item
        item_name = item["subject"]
        description = item["body"]
        city = item["geo"]["city"]["short_name"]
        insertion_date = item["dates"]["display"]

        images = ()
        all_images = item["images"]
        for image in all_images:
            for scale in image["scale"]:
                if scale["size"] == "big":
                    images += (scale["uri"],)

        # features
        features = item["features"]
        sold = "NO"
        shipping = True
        price = None

        for f in features:
            if f["uri"] == "/price":
                price = f["values"][0]["key"]
            if f["uri"] == "/transaction_status":
                sold = f["values"][0]["value"]
            if f["uri"] == "/item_shippable":
                if f["values"][0]["key"] == "0":
                    shipping = False
                else:
                    shipping = True

        url = item["urls"]["default"]
        item_info: dict = {
            "name": item_name,
            "description": description,
            "images": images,
            "date": insertion_date,
            "price": price,
            "sold": sold,
            "city": city,
            "shipping": shipping,
            "url": url,
        }
        return item_info
