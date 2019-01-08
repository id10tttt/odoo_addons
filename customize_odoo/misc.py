# -*- coding: utf-8 -*-
from . import pycompat
from collections import MutableMapping
from odoo.tools import misc
import logging

_logger = logging.getLogger(__name__)

# 从odoo12 里面剥出来
def clean_context(context):
    """ This function take a dictionary and remove each entry with its key starting with 'default_' """
    return {k: v for k, v in context.items() if not k.startswith('default_')}

@pycompat.implements_to_string
class StackMap(MutableMapping):
    """ A stack of mappings behaving as a single mapping, and used to implement
        nested scopes. The lookups search the stack from top to bottom, and
        returns the first value found. Mutable operations modify the topmost
        mapping only.
    """
    __slots__ = ['_maps']

    def __init__(self, m=None):
        self._maps = [] if m is None else [m]

    def __getitem__(self, key):
        for mapping in reversed(self._maps):
            try:
                return mapping[key]
            except KeyError:
                pass
        raise KeyError(key)

    def __setitem__(self, key, val):
        self._maps[-1][key] = val

    def __delitem__(self, key):
        del self._maps[-1][key]

    def __iter__(self):
        return iter({key for mapping in self._maps for key in mapping})

    def __len__(self):
        return sum(1 for key in self)

    def __str__(self):
        return u"<StackMap %s>" % self._maps

    def pushmap(self, m=None):
        self._maps.append({} if m is None else m)

    def popmap(self):
        return self._maps.pop()

misc.StackMap = StackMap
misc.clean_context = clean_context