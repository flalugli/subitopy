import asyncio

import aiohttp


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
        NUOVO: 10
        COME_NUOVO: 20
        OTTIME: 30
        BUONE: 40
        DANNEGGIATO: 50
