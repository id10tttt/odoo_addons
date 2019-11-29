#-*- coding: utf-8 -*-
from odoo.models import safe_eval, PGERROR_TO_OE, onchange_v7
from odoo import api, models, _
import psycopg2

@api.model
def _onchange_eval(self, field_name, onchange, result):
    """ Apply onchange method(s) for field ``field_name`` with spec ``onchange``
        on record ``self``. Value assignments are applied on ``self``, while
        domain and warning messages are put in dictionary ``result``.

        修改
        if not res or res == [None]:
            return
        添加 or res == [None]
    """
    onchange = onchange.strip()

    def process(res):
        if not res or res == [None]:
            return
        # try:
        if res.get('value'):
            res['value'].pop('id', None)
            self.update({key: val for key, val in res['value'].iteritems() if key in self._fields})
        if res.get('domain'):
            result.setdefault('domain', {}).update(res['domain'])
        if res.get('warning'):
            if result.get('warning'):
                # Concatenate multiple warnings
                warning = result['warning']
                warning['message'] = '\n\n'.join(filter(None, [
                    warning.get('title'),
                    warning.get('message'),
                    res['warning'].get('title'),
                    res['warning'].get('message'),
                ]))
                warning['title'] = _('Warnings')
            else:
                result['warning'] = res['warning']
        # except Exception,e:
        #     pass

    # onchange V8
    if onchange in ("1", "true"):
        for method in self._onchange_methods.get(field_name, ()):
            method_res = method(self)
            process(method_res)
        return

    # onchange V7
    match = onchange_v7.match(onchange)
    if match:
        method, params = match.groups()

        class RawRecord(object):
            def __init__(self, record):
                self._record = record

            def __getitem__(self, name):
                record = self._record
                field = record._fields[name]
                return field.convert_to_write(record[name], record)

            def __getattr__(self, name):
                return self[name]

        # evaluate params -> tuple
        global_vars = {'context': self._context, 'uid': self._uid}
        if self._context.get('field_parent'):
            record = self[self._context['field_parent']]
            global_vars['parent'] = RawRecord(record)
        field_vars = RawRecord(self)
        params = safe_eval("[%s]" % params, global_vars, field_vars, nocopy=True)

        # invoke onchange method
        method_res = getattr(self._origin, method)(*params)
        process(method_res)

models.Model._onchange_eval = _onchange_eval