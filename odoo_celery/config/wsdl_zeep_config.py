#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from requests import Session
from zeep.transports import Transport
from zeep import Client

session = Session()
session.verify = False
transport = Transport(session=session, timeout=30)


def get_zeep_client_session(url):
    return Client(url, transport=transport)
