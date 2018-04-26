# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import traceback
import time
import logging

_logger = logging.getLogger(__name__)


class FleetVehicleAccident(models.Model):
    _name = 'fleet.vehicle.accident'
    _description = u'车辆事故'

    name = fields.Char('fleet_accident_name', help='简述本次事故')
    accident_no = fields.Integer('accident_no', readonly=True, default=lambda self: self._compute_no())
    company_id = fields.Many2one('res.company', 'company_id', default=lambda self: self.env.user.company_id)

    accident_plate = fields.Many2one('fleet.vehicle', 'accident_plate', required=True, ondelete='restrict')
    accident_driver = fields.Many2one('hr.employee', 'accident_driver', required=True)
    accident_date = fields.Datetime('accident_date', required=True)
    accident_location = fields.Char('accident_location', required=True)

    accident_plate_opposite = fields.Char('accident_plate_opposite')

    is_fast_claims = fields.Selection([('yes', '是'), ('no', '否')], 'fast_claims', required=True)
    is_injuries_or_death = fields.Selection([('yes', '是'), ('no', '否')], 'is_injuries_or_death', required=True)
    responsible_owner = fields.Selection([('single_reason', u'单方责任'),
                                          ('opposite_reason', u'对方全责'),
                                          ('our_reason', u'我方全责')],
                                         required=True)
    accident_reason = fields.Text('accident_reason', required=True)

    repaire_factory = fields.Many2one('res.partner', 'repaire_factory')
    repaire_date = fields.Date('repaire_date')
    repaire_amount = fields.Float('repaire_amount')

    our_insurance = fields.Many2one('res.partner', 'our_insurance')
    deal_person = fields.Many2one('res.partner', 'deal_person')
    deal_amount = fields.Float('deal_amount')

    accident_pad_funded_ids = fields.One2many('fleet.vehicle.accident.pad.funded', 'fleet_accident_id', ondelete='restrict')

    insurance_claims_amount = fields.Float('insurance_claims_amount')
    insurance_claims_date = fields.Date('insurance_claims_date')
    insurance_claims_confirm = fields.Many2one('res.partner', 'insurance_claims_confirm')

    claims_note = fields.Text('claims_note')

    def _compute_no(self):
        res = self.env['fleet.vehicle.accident'].search([], order='id desc', limit=1)
        if res:
            return res.accident_no + 1
        else:
            return 1


class FleetVehicleAccidentPadFunded(models.Model):
    _name = 'fleet.vehicle.accident.pad.funded'
    _description = u'事故垫资情况'

    name = fields.Char('name', default=lambda self: self._compute_funded_name())
    pad_funded_time = fields.Date('pad_funded_time')
    pad_funded_amount = fields.Float('pad_funded_amount')
    pad_funded_account = fields.Many2one('account.account', 'pad_funded_account')
    pad_funded_journal = fields.Many2one('account.journal', 'pad_funded_journal')
    pad_funded_analytic_id = fields.Many2one('account.analytic.account', 'pad_funded_analytic_id')
    pad_funded_partner_id = fields.Many2one('res.partner', 'pad_funded_partner_id')

    fleet_accident_id = fields.Many2one('fleet.vehicle.accident', 'fleet_accident_id', ondelete='restrict')
    state = fields.Selection([('draft', '草稿'), ('submit', '已提交'), ('audit', '已审核')],
                             string=u'状态', index=True, readonly=True, default='draft')

    pad_funded_account_move = fields.Many2one('account.move', 'pad_funded_account_move')

    pad_funded_cash_id = fields.Many2one('core.value', 'pad_funded_cash_id')

    company_id = fields.Many2one('res.company', 'company_id', default=lambda self: self.env.user.company_id)

    @api.multi
    def commit_audit(self):
        self.state = 'submit'

    @api.multi
    def audit_pad_funded(self):
        account_move_data = {
            'journal_id': self.pad_funded_journal.id,
            'date': self.pad_funded_time,
            'period_id': self.env['account.period'].search(
                [('code', '=', self.compute_period(self.pad_funded_time))]).id,
            'company_id': self.company_id.id,
            'ref': self.name
        }


        res = self.env['account.move'].create(account_move_data)

        # 1121.04科目
        account_id = self.env['account.account'].search([('code', '=', '1221.04'),
                                                         ('company_id', '=', self.company_id.id)])
        if account_id:
            move_line_data = [
                (0, 0, {
                    'account_id': self.pad_funded_account.id,
                    'name': self.name,
                    'cash_id': self.pad_funded_cash_id.id,
                    'credit': self.pad_funded_amount,
                    'debit': 0,
                    'move_id': res.id
                }),
                (0, 0, {
                    'account_id': account_id.id,
                    'partner_id': self.pad_funded_partner_id.id,
                    'name': self.name,
                    'credit': 0,
                    'debit': self.pad_funded_amount,
                    'move_id': res.id
                })]

            res.write({'line_ids': move_line_data})

            self.env.cr.commit()

            self.state = 'audit'
            self.pad_funded_account_move = res.id

            _logger.info('{0} 于 {1} 审核'.format(self.env.user.name,
                                                    time.asctime(time.localtime(time.time()))))

            return res
        else:
            raise ValidationError('当前公司 {0}, 没有定义科目 [1221.04] !'.format(self.company_id.name))

    @api.multi
    def _compute_funded_name(self):
        res = self.env['fleet.vehicle.accident.pad.funded'].search([], order='id desc', limit=1)
        if res:
            return 'P/F/000' + str(res.id + 1)
        else:
            return 'P/F/000' + str(1)

    @api.multi
    def compute_period(self, date):
        return str(date)[5:7] + '/' + str(date)[:4]


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    vehicle_accident_ids = fields.One2many('fleet.vehicle.accident', 'accident_plate')
