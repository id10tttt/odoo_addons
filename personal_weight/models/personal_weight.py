#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from odoo import models, api, fields, _


class PersonalWeight(models.Model):
    _name = 'personal.weight'
    _rec_name = 'date'

    person = fields.Char('Person')
    date = fields.Date('Date')
    weight = fields.Float('Weight')
    am_pm_type = fields.Selection([
        ('am', 'AM'),
        ('pm', 'PM')
    ], string='A/PM')
