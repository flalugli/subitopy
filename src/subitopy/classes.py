import datetime
import statistics
from dataclasses import dataclass, field

from async_lru import alru_cache

from .utils import AsyncRequest


@dataclass(unsafe_hash=True)
class Advertiser:
    "class that represents a user that posted an ad for an item on subito.it"
    user_id: int
    is_company: bool

    @alru_cache(ttl=3600)  # we use maxsize=128 here so that if a page is scanned twice
    async def get_feedback(self, limit: int = 30, page_n: int = 0, proxy=None):
        asyncrequest = AsyncRequest(tries=3)
        user_type = "MEMBER" if not self.is_company else "COMPANY"

        url = f"https://feedback-api-subito.trust.advgo.net/public/users/sdrn:subito:user:{self.user_id}/feedback"
        query = {"limit": limit, "page": page_n, "sources": user_type}

        r = await asyncrequest.get(url=url, params=query, proxy=proxy)
        tot_reviews = r["reputation"]["sourceCounts"][
            "MEMBER"
        ]  # depends if subito re implements automatic reviews in that case watch ["reputation"]["receivedCount"]
        if tot_reviews > 30:
            pages = int(tot_reviews / 30)
        for page in range(pages):
            query["page"] = page + 1
            new_r = await asyncrequest.get(url=url, params=query, proxy=proxy)
            r["result"] += new_r["result"]

        return r

    async def reviews(self):
        r = await self.get_feedback()
        return r["result"]

    async def reputation(self):
        r = await self.get_feedback()
        return r["reputation"]


@dataclass(order=True)  # standard order is by price
class Item:
    "class to store item ads from the subito.it api"
    item_id: int
    name: str
    description: str
    price: int
    url: str
    date: datetime.datetime
    condition: str
    city: str
    sold: str  # this can have 3 options, that's why we keep it as str
    shipping: bool
    city: str
    advertiser: Advertiser
    images: tuple[str]

    def __post_init__(self):
        self.sort_index = self.price

    def check_strings(
        self,
        search_everywhere: list[str] = [],
        search_inname: list[str] = [],
        search_indescription: list[str] = [],
    ) -> bool:
        name_lower = self.name.lower()
        description_lower = self.description.lower()
        for s in search_everywhere:
            if s in name_lower or s in description_lower:
                return False
        for s in search_inname:
            if s in name_lower:
                return False
        for s in search_indescription:
            if s in description_lower:
                return False

        return True


@dataclass
class ItemCollection:
    "class to store collection of Item objects, useful for statistics on prices and for performing operations on Item objects"

    Itemlist: list[Item] = field(default_factory=list)
    items_number: int = field(init=False)

    def __post_init__(
        self,
    ):
        if len(self.Itemlist) > 0:
            self.items_number = len(self.Itemlist)

    def __iter__(self):
        return iter(self.Itemlist)

    def __add__(self, new_itemlist):
        final_itemlist = self.Itemlist + new_itemlist.Itemlist
        return ItemCollection(final_itemlist)

    def __getitem__(self, key: int):
        return self.Itemlist[key]

    def __setitem__(self, key: int, value: Item):
        self.Itemlist[key] = value
        self.__post_init__()  # check if this is even used ever

    def __len__(self):
        return len(self.Itemlist)

    def collection_append(self, new_item: Item):
        self.Itemlist.append(new_item)
        self.__post_init__()

    def stats(self):
        if self.items_number > 0:
            items_number = self.items_number
            items_prices = [x.price for x in self.Itemlist]
            mean_price = statistics.fmean(items_prices)
            median = statistics.median(items_prices)
            if self.items_number > 1:
                stdev = round(statistics.stdev(items_prices), 2)
            else:
                stdev = None

            stats_dict = {
                "tot_num": items_number,
                "mean_price": mean_price,
                "median": median,
                "stdev": stdev,
            }
            return stats_dict
        else:
            raise KeyError("No items were passed")

    def order_by_price(self):
        self.Itemlist.sort()

    def return_list_priceorder(self) -> list[Item]:
        return sorted(self.Itemlist)

    def return_list_timeorder(self) -> list[Item]:
        return sorted(self.Itemlist, key=lambda x: x.date.timestamp())

    def filter_strings(
        self,
        search_everywhere: list[str] = [],
        search_inname: list[str] = [],
        search_indescription: list[str] = [],
    ):
        "This function will return the matches that are also removed from the original collection"

        if (
            search_everywhere == []
            and search_inname == []
            and search_indescription == []
        ):
            return self.Itemlist

        filtered_items = []
        matches = []
        for item in self.Itemlist:
            if item.check_strings(
                search_everywhere=search_everywhere,
                search_inname=search_inname,
                search_indescription=search_indescription,
            ):
                filtered_items.append(item)
            else:
                matches.append(item)

        self.Itemlist = filtered_items
        self.__post_init__()
        return ItemCollection(matches)

    def remove_sold_items(self):
        self.Itemlist = [item for item in self.Itemlist if item.sold == "NO"]
        self.__post_init__()

    def pop_sold_items(self):
        sold_items = []
        unsold_items = []
        for item in self.Itemlist:
            if item.sold != "NO":
                sold_items.append(item)
            else:
                unsold_items.append(item)
        self.Itemlist = unsold_items
        self.__post_init__()
        return ItemCollection(sold_items)

    def filter_prices(self, minprice: int = 0, maxprice: int = None):
        new_items = []
        for item in self.Itemlist:
            if maxprice == None:
                if item.price >= minprice:
                    new_items.append(item)
            else:
                if minprice < item.price < maxprice:
                    new_items.append(item)

        self.Itemlist = new_items
        self.__post_init__()

    def remove_noshipping(self):
        self.Itemlist = [item for item in self.Itemlist if item.shipping == True]

        self.__post_init__()
