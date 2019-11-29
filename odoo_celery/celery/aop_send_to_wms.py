# /usr/bin/env python3
# -*- coding: utf-8 -*-
from celery import Celery
import logging
import json
try:
    from ..config import send_to_wms_config
    from ..config.wsdl_zeep_config import get_zeep_client_session
except:
    import send_to_wms_config
    from wsdl_zeep_config import get_zeep_client_session


_logger = logging.getLogger(__name__)


# config celery: backend and broker
app = Celery('aop_send_to_wms')
app.config_from_object(send_to_wms_config)


# use celery when send data
@app.task(max_retries=5, retry_backoff=True, name='send_stock_picking_to_wms_task')
def send_stock_picking_to_wms(task_url, data):
    zeep_stock_picking_client = get_zeep_client_session(task_url)
    _logger.info({
        'data': data
    })
    # send stock picking data(WSDL)
    zeep_stock_picking_client.service.sendToTask(json.dumps(data, ensure_ascii=False))
