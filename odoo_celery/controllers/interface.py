# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import content_disposition, dispatch_rpc, request, Response

import logging
import json
import time
from odoo.tools import config
from ..celery.aop_receive_from_wms import aop_receive_from_wms

_logger = logging.getLogger(__name__)


class TestInterface(http.Controller):

    # You can also use @http.route('/api/<string:model>/done_picking'
    @http.route('/api/stock_picking/done_picking', methods=["POST"], type='json', auth='none', csrf=False)
    def done_picking(self, **post):
        msg = {
            'code': 200,
            'method': '/api/stock_picking/done_picking',
            'time': time.time(),
        }
        self._done_picking(post.get('data'))
        return json.dumps(msg)

    def _done_picking(self, data):
        # FIXME: for multi database, you must define the db or you can't get session correctly.
        db_name = config.get('interface_db_name')
        request.session.db = db_name

        # Get celery config in odoo.conf
        username = config.misc.get("celery", {}).get('user_name')
        password = config.misc.get("celery", {}).get('user_password')
        url = config.misc.get("celery", {}).get('url')

        # define the database
        db_name = db_name

        # define your model name
        model_name = 'done.picking.log'
        method_name = 'create'

        # Put task to celery
        aop_receive_from_wms.delay(
            url=url,
            db=db_name,
            username=username,
            password=password,
            model=model_name,
            method=method_name,
            data=data
        )

