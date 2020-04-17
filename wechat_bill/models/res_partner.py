#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.one
    def get_current_record(self):
        print(self)

    @api.multi
    def get_current_records(self):
        print(self)
