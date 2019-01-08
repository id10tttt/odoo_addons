#-*- coding: utf-8 -*-
from odoo import models, api
from . import pycompat
from odoo.fields import Field, Many2many, One2many
import logging

_logger = logging.getLogger(__name__)


def convert_to_column_multi(self, value, record, values=None, validate=True):
    # _logger.info('patched convert_to_column')
    """ Convert ``value`` from the ``write`` format to the SQL format. """
    if value is None or value is False:
        return None
    return pycompat.to_native(value)

def field_type_get(self):
    pass

Field.convert_to_column_multi = convert_to_column_multi
Field.field_type_get = field_type_get
