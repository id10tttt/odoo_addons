#-*- coding: utf-8 -*-
from odoo import models, api
from . import pycompat
from odoo.fields import Field, Many2many, One2many


def create_multi(self, record_values):
    if not record_values:
        return

    model = record_values[0][0]
    comodel = model.env[self.comodel_name].with_context(**self.context)
    inverse = self.inverse_name
    vals_list = []                  # vals for lines to create in batch

    def flush():
        if vals_list:
            # comodel.create(vals_list)
            comodel.create_multi(vals_list)
            # vals_list.clear()
            for vals in vals_list:
                vals.clear()

    def drop(lines):
        if comodel._fields[inverse].ondelete == 'cascade':
            lines.unlink()
        else:
            lines.write({inverse: False})

    with model.env.norecompute():
        for record, value in record_values:
            for act in (value or []):
                if act[0] == 0:
                    vals_list.append(dict(act[2], **{inverse: record.id}))
                elif act[0] == 1:
                    comodel.browse(act[1]).write(act[2])
                elif act[0] == 2:
                    comodel.browse(act[1]).unlink()
                elif act[0] == 3:
                    drop(comodel.browse(act[1]))
                elif act[0] == 4:
                    line = comodel.browse(act[1])
                    line_sudo = line.sudo().with_context(prefetch_fields=False)
                    if int(line_sudo[inverse]) != record.id:
                        line.write({inverse: record.id})
                elif act[0] == 5:
                    flush()
                    domain = self.domain(record) if callable(self.domain) else self.domain
                    domain = domain + [(inverse, '=', record.id)]
                    drop(comodel.search(domain))
                elif act[0] == 6:
                    flush()
                    comodel.browse(act[2]).write({inverse: record.id})
                    domain = self.domain(record) if callable(self.domain) else self.domain
                    domain = domain + [(inverse, '=', record.id), ('id', 'not in', act[2] or [0])]
                    drop(comodel.search(domain))

        flush()

One2many.create_multi = create_multi