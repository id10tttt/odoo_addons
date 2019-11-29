#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from requests import Session
from zeep.transports import Transport
from zeep import Client

session = Session()
session.verify = False
transport = Transport(session=session, timeout=30)

SUPPLIER_FIELD_DICT = {
    'name': 'name',
    'ref': 'code',
    'country_id': 'country_name',
    'state_id': 'state_name',
    'city_id': 'city_name',
    'district_id': 'district_name',
    'street': 'street_name'
}


def get_zeep_client_session(url):
    return Client(url, transport=transport)
