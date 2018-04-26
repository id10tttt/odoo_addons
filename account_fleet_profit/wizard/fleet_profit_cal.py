# -*- coding: utf-8 -*-
import json
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.osv import *
from odoo.exceptions import UserError, ValidationError, Warning
import traceback
import logging

_logger = logging.getLogger(__name__)


class FleetProfitWizard(models.Model):
    _name = 'fleet.profit.wizard'
    _description = u'输出当天车辆收入和支出'

    start_date = fields.Date(
        string=u'开始日期',
        required=True,
        default=fields.Date.context_today,
    )
    end_date = fields.Date(
        string=u'截止日期',
        required=True,
        default=fields.Date.context_today,
    )
    company_id = fields.Many2one(
        'res.company',
        string=u'公司',
        change_default=True,
        default=lambda self: self.env['res.company']._company_default_get())

    def calculate_fleet_profit(self):
        try:
            from_date = self.start_date
            to_date = next_day(self.end_date)

            income_res = self.env['account.invoice'].search([('type', '=', 'out_invoice'),
                                                             ('company_id', '=', self.company_id.id),
                                                             ('state', '=', 'open')])
            fleet_vehicle = self.env['fleet.vehicle'].search([('company_id', '=', self.company_id.id)])
            if not fleet_vehicle:
                raise UserError('当前公司下无车辆')
            request = ('''
                           SELECT a.id as fleet_id,
                                  SUM(l.price_subtotal) AS price_subtotal,
                                  to_date(cast(l.write_date as TEXT), 'yyyy-mm-dd') AS write_date
                           FROM fleet_vehicle AS a JOIN account_invoice_line AS l
                                ON a.id = l.vehicle_id AND
                                   a.id IN %s AND
                                   l.invoice_id in %s AND
                                   l.vehicle_id IN %s AND 
                                   l.write_date >= %s AND 
                                   l.write_date < %s
                           WHERE a.company_id = %s
                           GROUP BY a.id,
                                    l.write_date
                       '''
                       )
            params = (tuple(fleet_vehicle.ids),
                      tuple(income_res.ids),
                      tuple(fleet_vehicle.ids),
                      from_date, to_date,
                      self.company_id.id)
            self.env.cr.execute(request, params)
            sql_income_res = self.env.cr.dictfetchall()

            # print 'sql_income_res: ', sql_income_res, '\n\n\n\n'
            cost_res = self.env['account.invoice'].search([('type', '=', 'in_invoice'),
                                                           ('state', '=', 'open'),
                                                           ('company_id', '=', self.company_id.id)])
            request = ('''
                        SELECT a.id as fleet_id,
                                  SUM(l.price_subtotal) AS total_amount,
                                  to_date(cast(l.write_date as TEXT), 'yyyy-mm-dd') AS write_date
                           FROM fleet_vehicle AS a JOIN account_invoice_line AS l
                                ON a.id = l.vehicle_id AND
                                   a.id IN %s AND
                                   l.invoice_id in %s AND
                                   l.vehicle_id IN %s AND 
                                   l.write_date >= %s AND 
                                   l.write_date < %s
                           WHERE a.company_id = %s
                           GROUP BY a.id,
                                    l.write_date
                       '''
                       )
            params = (tuple(fleet_vehicle.ids), tuple(cost_res.ids), tuple(fleet_vehicle.ids), from_date, to_date,
                      self.company_id.id)

            self.env.cr.execute(request, params)
            sql_cost_res = self.env.cr.dictfetchall()
            # print 'sql_cost_res: ', sql_cost_res, '\n\n\n'
            hr_expense = self.env['hr.expense.sheet'].search([('company_id', '=', self.company_id.id),
                                                              ('accounting_date', '>=', from_date),
                                                              ('accounting_date', '<', to_date),
                                                              ('state', '!=', 'submit')])
            if not hr_expense:
                raise UserError('在这段期间没有车辆数据!')
            request = ('''
                        SELECT a.id as fleet_id,
                                  SUM(h.unit_amount) AS total_amount,
                                  h.date AS write_date
                           FROM fleet_vehicle AS a JOIN hr_expense as h
                                ON a.id = h.vehicle_id AND
                                   a.id IN %s AND
                                   h.sheet_id in %s AND
                                   h.vehicle_id IN %s AND 
                                   h.date >= %s AND
                                   h.date < %s
                           WHERE a.company_id = %s
                           GROUP BY a.id,
                                    h.date
                       '''
                       )
            params = (tuple(fleet_vehicle.ids),
                      tuple(hr_expense.ids),
                      tuple(fleet_vehicle.ids),
                      from_date, to_date,
                      self.company_id.id)

            self.env.cr.execute(request, params)
            sql_sum_cost_res = self.env.cr.dictfetchall()
            print 'sql_sum_cost_res: ', sql_sum_cost_res, '\n\n\n\n'

            res_cost = {}
            data = []
            for item in (sql_cost_res + sql_sum_cost_res):
                res_cost.setdefault(item['write_date'], []).append(item)

            for x in res_cost:
                tmp = {}
                for item in res_cost[x]:
                    tmp.setdefault(item['fleet_id'], []).append(item)
                for y in tmp:
                    data.append({'write_date': x, 'fleet_id': y, 'total_amount': sum(z['total_amount'] for z in tmp[y])})

            data_res = {}
            for item in (sql_income_res + data):
                data_res.setdefault(item['write_date'], []).append(item)
            data_fin = []
            for x in data_res:
                tmp = {}
                for item in data_res[x]:
                    tmp.setdefault(item['fleet_id'], []).append(item)
                for y in tmp:
                    data_fin.append({'write_date': x,
                                 'fleet_id': y,
                                 'price_subtotal': sum(z['price_subtotal'] for z in tmp[y] if 'price_subtotal' in z),
                                 'total_amount': sum(z['total_amount'] for z in tmp[y] if 'total_amount' in z)})
            self.env['fleet.profit'].search([('vehicle_date', '>=', from_date),('vehicle_date', '<', to_date)]).unlink()

            for x in data_fin:
                income = round(x['price_subtotal'], 2)
                cost_f = round(x['total_amount'], 2)
                data = {
                    'vehicle_fleet': x['fleet_id'],
                    'vehicle_income': income,
                    'vehicle_cost': cost_f,
                    'vehicle_date': x['write_date'],
                    'vehicle_profit': income - cost_f
                }
                res = self.env['fleet.profit']
                res.create(data)
            self.env.cr.commit()
        except Exception:
            raise UserError(traceback.format_exc())


def next_day(time):
    tmp = datetime.strptime(time, '%Y-%m-%d')
    tmp = tmp + timedelta(days = 1)
    return tmp.strftime('%Y-%m-%d')