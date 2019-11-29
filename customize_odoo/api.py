#-*- coding: utf-8 -*-
from odoo import api
from decorator import decorate, decorator
from odoo.api import Environment, contextmanager
import sys
from collections import  Mapping
import logging
from .misc import StackMap
_logger = logging.getLogger(__name__)


def _model_create_multi(obj, self, arg):
    # 'create' expects a list of dicts and returns a recordset
    if isinstance(arg, Mapping):
        return obj(self, [arg])
    return obj(self, arg)


def model_create_multi(method):
    """ Decorate a method that takes a list of dictionaries and creates multiple
        records. The method may be called with either a single dict or a list of
        dicts::

            record = model.create(vals)
            records = model.create([vals, ...])
    """
    wrapper = decorate(method, _model_create_multi)
    wrapper._api = 'model_create'
    return wrapper


@contextmanager
def protecting_multi(self, what, records=None):
    """ Prevent the invalidation or recomputation of fields on records.
        The parameters are either:
         - ``what`` a collection of fields and ``records`` a recordset, or
         - ``what`` a collection of pairs ``(fields, records)``.
    """
    protected = self._protected
    protected = StackMap(protected)
    try:
        protected.pushmap()
        what = what if records is None else [(what, records)]
        for fields, records in what:
            for field in fields:
                ids = protected.get(field, frozenset())
                protected[field] = ids.union(records._ids)
        yield
    finally:
        protected.popmap()

api._model_create_multi = _model_create_multi
api.model_create_multi = model_create_multi
api.Environment.protecting_multi = protecting_multi

