# -*- coding: utf-8 -*-

from odoo import models, fields, api

class LoanGroup(models.Model):
    _inherit = 'credit.loan.group'

    event_registration_ids = fields.One2many('event.registration','group_id','Information Meetings')

class Event(models.Model):
    _inherit = 'event.event'

class EventType(models.Model):
    _inherit = 'event.type'

class EventRegistration(models.Model):
    _inherit = 'event.registration'

    financing_id = fields.Many2one()
    group_id = fields.Many2one('credit.loan.group','Group', compute='set_group',store=True)

    @api.depends('partner_id')
    def set_group(self):
        for rec in self:
            rec.group_id = self.env['credit.loan.group'].search([('partner_id.id','=',rec.partner_id.id),('status','=','draft')], limit=1, order='date_organized desc')

