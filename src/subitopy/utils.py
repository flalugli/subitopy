import asyncio
import datetime
import statistics
from dataclasses import dataclass, field

import aiohttp
from async_lru import alru_cache


class QueryParameters:

    class Categories:

        MOTORI = 1
        AUTO = 2
        MOTO_E_SCOOTER = 3
        VEICOLI_COMMERCIALI = 4
        ACCESSORI_AUTO = 5
        IMMOBILI = 6
        APPARTAMENTI = 7
        UFFICI_E_LOCALI_COMMERCIALI = 8
        ELETTRONICA = 9
        INFORMATICA = 10
        AUDIO_VIDEO = 11
        TELEFONIA = 12
        PER_LA_CASA_E_LA_PERSONA = 13
        ARREDAMENTO_E_CASALINGHI = 14
        GIARDINO_E_FAI_DA_TE = 15
        ABBIGLIAMENTO_E_ACCESSORI = 16
        TUTTO_PER_I_BAMBINI = 17
        SPORTS_E_HOBBY = 18
        MUSICA_E_FILM = 19
        SPORTS = 20
        COLLEZIONISMO = 21
        NAUTICA = 22
        ANIMALI = 23
        LAVORO_E_SERVIZI = 24
        ATTREZZATURE_DI_LAVORO = 25
        OFFERTE_DI_LAVORO = 26
        ALTRI = 28
        VILLE_SINGOLE_E_A_SCHIERA = 29
        TERRENI_E_RUSTICI = 30
        GARAGE_E_BOX = 31
        LOFT_MANSARDE_E_ALTRO = 32
        CASE_VACANZA = 33
        CARAVAN_E_CAMPER = 34
        ACCESSORI_MOTO = 36
        ELETTRODOMESTICI = 37
        LIBRI_E_RIVISTE = 38
        STRUMENTI_MUSICALI = 39
        FOTOGRAFIA = 40
        BICICLETTE = 41
        CANDIDATI_IN_CERCA_DI_LAVORO = 42
        CAMERE_POSTI_LETTO = 43
        CONSOLE_E_VIDEOGIOCHI = 44
        SERVIZI = 50
        EMPTY = ""

    class Regions:

        VALLE_DAOSTA = 1
        PIEMONTE = 2
        LIGURIA = 3
        LOMBARDIA = 4
        TRENTINO_ALTO_ADIGE = 5
        VENETO = 6
        FRIULI_VENEZIA_GIULIA = 7
        EMILIA_ROMAGNA = 8
        TOSCANA = 9
        UMBRIA = 10
        LAZIO = 11
        MARCHE = 12
        ABRUZZO = 13
        MOLISE = 14
        CAMPANIA = 15
        PUGLIA = 16
        BASILICATA = 17
        CALABRIA = 18
        SARDEGNA = 19
        SICILIA = 20
        EMPTY = 0

    class Sort:

        DATE = "datedesc"
        LOWEST_PRICE = "priceasc"
        HIGHEST_PRICE = "pricedesc"

    class Ad_Type:

        FOR_SALE = "s"
        WANTED = "k"

    class Conditions:
        COME_NUOVO: 10
        OTTIME: 20
        BUONE: 30
        DANNEGGIATO: 40


class AsyncRequest:
    def __init__(self, tries: int = 3, timeout: int = 1) -> None:
        self.tries = tries
        self.timeout = timeout

    async def request(
        self, request_type: str, url, *args, **kwargs
    ) -> aiohttp.ClientResponse | None:

        i = 0
        async with aiohttp.ClientSession(raise_for_status=False) as session:
            while i < self.tries:
                if request_type == "get":
                    async with session.get(url=url, *args, **kwargs) as result:
                        status = result.status
                        if status < 400:
                            return await result.json()

                elif request_type == "post":
                    async with session.post(url=url, *args, **kwargs) as result:
                        status = result.status
                        if status < 400:
                            return result

                i += 1
                await asyncio.sleep(self.timeout)

    async def get(self, url: str, *args, **kwargs) -> aiohttp.ClientResponse | None:
        return await self.request(request_type="get", url=url, *args, **kwargs)


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
    descritpion: str
    price: int
    url: str
    date: datetime.datetime
    condition: str
    city: str
    sold: str #this can have 3 options, that's why we keep it as str
    shipping: bool
    city: str
    advertiser: Advertiser
    images: tuple[str]

    def __post_init__(self):
        self.sort_index = self.price

    def check_strings(
        self,
        search_everywhere: list[str],
        search_inname: list[str] = [],
        search_indescription: list[str] = [],
    ) -> bool:
        name_lower = self.name.lower()
        description_lower = self.descritpion.lower()
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

        if (
            search_everywhere == []
            and search_inname == []
            and search_indescription == []
        ):
            return self.Itemlist

        filtered_items = []
        for item in self.Itemlist:
            if item.check_strings(
                search_everywhere=search_everywhere,
                search_inname=search_inname,
                search_indescription=search_indescription,
            ):
                filtered_items.append(item)

        return ItemCollection(Itemlist=filtered_items)

    def remove_sold_items(self):
        for item in self.Itemlist:
            if item.sold != "NO":
                self.Itemlist.remove(item)

    def pop_sold_items(self):
        sold_items = []
        for item in self.Itemlist:
            if item.sold != "NO":
                sold_items.append(item)
                self.Itemlist.remove(item)
        return ItemCollection(sold_items)
    
    def filter_prices(self, minprice:int = 0 ,maxprice:int = None):
        new_items = []
        for item in self.Itemlist:
            if maxprice == None:
                if item.price >= minprice:
                    new_items.append(item)
            else:
                if minprice < item.price < maxprice:
                    new_items.append(item)

        return ItemCollection(new_items)    

    def remove_noshipping(self):
        for item in self.Itemlist:
            if not item.shipping:
                self.Itemlist.remove(item)
            