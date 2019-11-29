#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from celery import Celery
import logging
from xmlrpc import client as xmlrpc_client

try:
    from ..config import receive_from_wms
except:
    import receive_from_wms

_logger = logging.getLogger(__name__)


app = Celery('aop_receive_from_wms')
app.config_from_object(receive_from_wms)


# Use Odoo RPC
@app.task(name='aop_receive_from_wms')
def aop_receive_from_wms(url=False, db=False, username=False, password=False, model=False, method=False, data=False):
    try:
        # use odoo rpc to execute
        common = xmlrpc_client.ServerProxy('{}/xmlrpc/2/common'.format(url))
        models = xmlrpc_client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        uid = common.authenticate(db, username, password, {})

        res = models.execute_kw(db, uid, password, model, method, data)
        _logger.info({
            'create': res
        })
    except:
        import traceback
        raise traceback.format_exc()
