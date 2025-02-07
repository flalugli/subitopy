import asyncio
import math
from datetime import datetime
from itertools import chain

from .errors import MunicipalityError
from .utils import AsyncRequest, Item, ItemCollection, QueryParameters, Advertiser


class Search:
    "wrapper for the subito.it search API"

    def __init__(
        self,
        base_url: str = "https://www.subito.it",
        api_version: int = 1,
        proxy: str | None = None,
    ) -> None:
        """
        Parameters
        ----------
        base_url : _type_, optional
            url for api calls, by default "https://www.subito.it"
        api_version : int, optional
            api version you want to use, by default 1
        proxy : str | None, optional
            proxy, if passed all the requests will be made passing through this proxy , by default None

        """

        self.api_version = api_version
        self.base_url = base_url

        self.search_api_url = self.base_url + f"/hades/v{api_version}/search/items"
        self.proxy = proxy
        self.request = AsyncRequest(tries=3)

    def _bool2query(self, arg: bool) -> str:
        """Transforms bool to query parameters

        Parameters
        ----------
        arg : bool
            boolean to transform

        Returns
        -------
        str
            query string

        Raises
        ------
        MunicipalityError

        """

        # TODO add checks
        result = str(arg).lower()

        return result

    async def get_page(self, query: dict, items_only: bool = True) -> dict:
        """fetches a subito.it page given a query and it's item insertion

        Parameters
        ----------
        query : dict
            request query
        items_only : bool, optional
            if set to True the function will return only item ads, by default True

        Returns
        -------
        dict
            a dictionary containing every item ad

        Raises
        ------
        MunicipalityError

        """
        page: dict = await self.request.get(
            url=self.search_api_url, params=query, proxy=self.proxy
        )

        if items_only:
            return page["ads"]
        else:
            return page

    async def get_page_short(self, query: dict) -> ItemCollection:
        """Returns the items in a page (list of 100 items) from the subito api as a collection of Item objects

        Parameters
        ----------
        query : dict
            query passed to the api, for formatting references please check the search function

        Returns
        -------
        ItemCollection
            Collection of the items in the page with their attributes

        Raises
        ------
        MunicipalityError

        """
        # get page of items with short info about them

        page = await self.get_page(query)
        items = []
        for item in page:
            item_shortinfo = self.get_item_shortinfo(item)
            items.append(item_shortinfo)

        page_short = ItemCollection(items)

        return page_short

    async def count_all_items(self, query: dict) -> int:
        """counts all items in a page and returns the corresponding integer

        Parameters
        ----------
        query : dict
            request query

        Returns
        -------
        int
            number of items in the page

        Raises
        ------
        MunicipalityError

        """
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
        titlesearch_only: bool = True,  # this is False by standard on the site but it narrows down the research
        shipping_only: bool = False,
        municipality: str = "",
        pages: int | str = 1,
        startingpage: int = 0,
        short: bool = True,
    ) -> list | ItemCollection:
        """search api call

        Parameters
        ----------
        itemname : str
            name of the item to research, it's the ad title
        category : int | str, optional
            category to which the item belongs, accepts QueryParameters.Categories, by default QueryParameters.Categories.EMPTY
        page_results : int, optional
            number of results per page, can vary from 0 to 100, by default 100
        sort_by : int | str, optional
            determines how the matches will be sorted, accepts QueryParameters.Sort, by default QueryParameters.Sort.DATE
        ad_type : int | str, optional
            ad type, can be for sale or wanting, accepts QueryParameters.Ad_Type, by default QueryParameters.Ad_Type.FOR_SALE
        region : int | str, optional
            region where the ad is located, accepts QueryParameters.Regions, by default QueryParameters.Regions.EMPTY
        titlesearch_only : bool, optional
            if set to true all the searches will have to match the words in the title, otherwise they can also match the description, by default True
        municipality : str, optional
            the municipality where the ad is located, by default ""
        pages : int | str, optional
            number of pages retrieved by the api, it's suggested to limit of pages fetched as this could cause ip limitations, if you want to retrieve all the pages set this to 'all', by default 1
        startingpage : int, optional
            the starting page, by default 0
        short : bool, optional
            if set to true the function will perform the get_item_shortinfo function on every item ad, by default True

        Returns
        -------
        list | ItemCollection
            a collection of Item object that automatically performs some statistics on the item prices whenever a new object is added

        Raises
        ------
        MunicipalityError

        """
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
                "qso": self._bool2query(titlesearch_only),
                "shp": self._bool2query(shipping_only),
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
                "qso": self._bool2query(titlesearch_only),
                "shp": self._bool2query(shipping_only),
                "sort": sort_by,
                "start": startingpoint,
                "lim": endpoint,
            }
            if short:
                r = self.get_page_short(query)
                tasks.append(asyncio.ensure_future(r))
                results = await asyncio.gather(*tasks)
                item_list = list(chain(*results))
                data = ItemCollection(
                    item_list
                )  # get items from each page all in 1 ItemCollection
            else:
                tasks.append(asyncio.ensure_future(self.get_page(query)))
                results = await asyncio.gather(*tasks)
                data = list(
                    chain(*results)
                )  # get items from each page all in one array

        return data

    async def get_advertiser_reviews(self, advertiser:Advertiser, limit:int = 30, page_n:int=0):
        user_type = "MEMBER" if not advertiser.is_company else "COMPANY"
        
        url = f"https://feedback-api-subito.trust.advgo.net/public/users/sdrn:subito:user:{advertiser.user_id}/feedback"
        query = {
            "limit" : limit,
            "page" : page_n,
            "sources" : user_type
        }
        
        r = await self.request.get(url=url, params=query , proxy=self.proxy)
        
        return r

    def get_item_shortinfo(self, item: dict) -> Item:
        """transforms a standard subito.it item ad in json format to a Item object

        Parameters
        ----------
        item : dict
            item ad passed as a python dictionary

        Returns
        -------
        Item
            item transformed to a python object
        """

        item_name = item["subject"]
        description = item["body"]
        city = item["geo"]["city"]["short_name"]
        insertion_date = item["dates"]["display"]
        
        adv_dict = item["advertiser"]
        is_company= True if adv_dict["company"] == True else False
        advertiser = Advertiser(user_id=adv_dict["user_id"],is_company=is_company)

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
        price = 0
        condition = "Sconosciuta"

        for f in features:
            if (
                f["uri"] == "/price" and price == 0
            ):  # and avoids going through the checks if the value has been found
                price = int(f["values"][0]["key"])
            if f["uri"] == "/transaction_status" and sold == "NO":
                sold = f["values"][0]["value"]
            if f["uri"] == "/item_condition":
                condition = f["values"][0]["value"]
            if f["uri"] == "/item_shippable":
                if f["values"][0]["key"] == "0":
                    shipping = False
                else:
                    shipping = True

        url = item["urls"]["default"]
        item_info: Item = Item(
            name=item_name,
            descritpion=description,
            images=images,
            date=datetime.strptime(insertion_date, "%Y-%m-%d %H:%M:%S"),
            price=price,
            sold=sold,
            condition=condition,
            city=city,
            shipping=shipping,
            advertiser=advertiser,
            url=url,
        )
        return item_info
