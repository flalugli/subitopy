import asyncio
import datetime
import statistics
from dataclasses import dataclass, field

import aiohttp


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

    categories = {
        "MOTORI": 1,
        "Auto": 2,
        "Moto e Scooter": 3,
        "Veicoli commerciali": 4,
        "Accessori Auto": 5,
        "IMMOBILI": 6,
        "Appartamenti": 7,
        "Uffici e Locali commerciali": 8,
        "ELETTRONICA": 9,
        "Informatica": 10,
        "Audio/Video": 11,
        "Telefonia": 12,
        "PER LA CASA e LA PERSONA": 13,
        "Arredamento e Casalinghi": 14,
        "Giardino e Fai da te": 15,
        "Abbigliamento e Accessori": 16,
        "Tutto per i bambini": 17,
        "SPORTS E HOBBY": 18,
        "Musica e Film": 19,
        "Sports": 20,
        "Collezionismo": 21,
        "Nautica": 22,
        "Animali": 23,
        "LAVORO E SERVIZI": 24,
        "Attrezzature di lavoro": 25,
        "Offerte di lavoro": 26,
        "Altri": 28,
        "Ville singole e a schiera": 29,
        "Terreni e rustici": 30,
        "Garage e box": 31,
        "Loft, mansarde e altro": 32,
        "Case vacanza": 33,
        "Caravan e Camper": 34,
        "Accessori Moto": 36,
        "Elettrodomestici": 37,
        "Libri e Riviste": 38,
        "Strumenti Musicali": 39,
        "Fotografia": 40,
        "Biciclette": 41,
        "Candidati in cerca di lavoro": 42,
        "Camere/Posti letto": 43,
        "Console e Videogiochi": 44,
        "Servizi": 50,
    }

    sort_by = {
        "date": "datedesc",
        "lowest price": "priceasc",
        "highest price": "pricedesc",
    }

    ad_type = {"for sale": "s", "wanted": "k"}

    regions = {
        "valle d'aosta": 1,
        "piemonte": 2,
        "liguria": 3,
        "lombardia": 4,
        "trentino alto adige": 5,
        "veneto": 6,
        "friuli venezia giulia": 7,
        "emilia romagna": 8,
        "toscana": 9,
        "umbria": 10,
        "lazio": 11,
        "marche": 12,
        "abruzzo": 13,
        "molise": 14,
        "campania": 15,
        "puglia": 16,
        "basilicata": 17,
        "calabria": 18,
        "sardegna": 19,
        "sicilia": 20,
        "": "",
    }


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


@dataclass(order=True)  # standard order is by price
class Item:
    name: str
    descritpion: str
    images: str
    date: datetime.datetime
    city: str
    price: int
    sold: str
    shipping: bool
    city: str
    url: str

    def __post_init__(self):
        self.sort_index = self.price


@dataclass
class ItemCollection:

    Itemlist: list[Item] = field(default_factory=list)
    items_number: int = field(init=False)
    mean_price: int = field(init=False)

    def __iter__(self):
        return iter(self.Itemlist)

    def __add__(self, new_itemlist):
        final_itemlist = self.Itemlist + new_itemlist.Itemlist
        return ItemCollection(final_itemlist)

    def __getitem__(self, key: int):
        return self.Itemlist[key]

    def __setitem__(self, key: int, value: Item):
        self.Itemlist[key] = value
        self.__post_init__()

    def __len__(self):
        return len(self.Itemlist)

    # add __radd__ method if needed

    def __post_init__(self):
        if len(self.Itemlist) > 0:
            self.items_number = len(self.Itemlist)
            self.mean_price = statistics.fmean([x.price for x in self.Itemlist])

    def collection_append(self, new_item: Item):
        self.Itemlist.append(new_item)
        self.__post_init__()

    def order_by_price(self):
        self.Itemlist.sort()

    def return_list_priceorder(self) -> list[Item]:
        return sorted(self.Itemlist)

    def return_list_timeorder(self) -> list[Item]:
        return sorted(self.Itemlist, key=lambda x: x.date.timestamp())
