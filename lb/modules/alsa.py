from datetime import date, datetime
from typing import List
import attr
import maya
from requests_html import HTMLSession
from lb.data_classes.response_journey import ResponseJourney  # todo

from lb.modules.provider_base import Provider


@attr.s
class Alsa(Provider):
    s = attr.ib(factory=HTMLSession)

    def get_destinations(self) -> dict:
        r = self.s.get("https://www.alsa.com/en/web/bus/home")
        r = self.s.get(
            "https://www.alsa.com/en/c/portal/layout?p_l_id=70167&p_p_cacheability=cacheLevelPage&p_p_id=JourneySearchPortlet_WAR_Alsaportlet&p_p_lifecycle=2&p_p_resource_id=JsonGetOrigins&locationMode=1&_=1536402460713"
        )

        return r.json()

    def _prase_data(self, raw_data: dict) -> List[ResponseJourney]:
        return [
            ResponseJourney(
                departure_datetime=maya.parse(journey.get("departureDataToFilter")).datetime(),
                arrival_datetime=maya.parse(journey.get("arrivalDataToFilter")).datetime(),
                source=journey.get("originName"),
                destination=journey.get("destinationName"),
                price=journey.get("fares")[0].get("price"),
                currency="EUR",
            )
            for journey in raw_data.get("journeys")
        ]

    def _get_routes(self, src: dict, dst: dict, when: date) -> dict:
        query = {
            "accessible": "0",
            "code": "",
            "p_p_state": "normal",
            "passengerType-4": "0",
            "_returnDate": "",
            "originStationNameId": src.get("name"),
            "destinationStationNameId": dst.get("name"),
            "originStationId": src.get("id"),
            "destinationStationId": dst.get("id"),
            "jsonAlsaPassPassenger": "",
            "departureDate": when.strftime("%m/%d/%Y"),
            "locationMode": "1",
            "p_p_col_count": "3",
            "passengerType-1": "1",
            "passengerType-2": "0",
            "passengerType-3": "0",
            "returnDate": "",
            "passengerType-5": "0",
            "travelType": "OUTWARD",
            "_departureDate": when.strftime("%m/%d/%Y"),
            "p_p_id": "PurchasePortlet_WAR_Alsaportlet",
            "numPassengers": "1",
            "regionalZone": "",
            "LIFERAY_SHARED_isTrainTrip": "false",
            "p_p_lifecycle": "1",
            "serviceType": "",
            "jsonVoucherPassenger": "",
            "_PurchasePortlet_WAR_Alsaportlet_javax.portlet.action": "searchJourneysAction",
            "promoCode": "",
            "p_p_mode": "view",
            "p_p_col_id": "column-1",
            "p_auth": "khT041BH",
        }
        r = self.s.get("https://www.alsa.com/en/web/bus/checkout", params=query)
        next_url = r.html.find("data-sag-journeys-component", first=True).attrs.get("sag-journeys-table-body-url")
        r = self.s.get(next_url)
        return self._prase_data(r.json())

    def get_routes(
        self, source: str, destination: str, departure: date = None, arrival: date = None
    ) -> List[ResponseJourney]:
        dests = self.get_destinations()

        source = f"{source} (all stops)"
        destination = f"{destination} (all stops)"

        for d in dests:
            if source.lower() in d.get("name").lower():
                src = d
            if destination.lower() in d.get("name").lower():
                dst = d

        return self._get_routes(src, dst, departure)
