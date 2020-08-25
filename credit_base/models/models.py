# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging

_logger = logging.getLogger(__name__)
class LoanFinancing(models.Model):
    _name = 'credit.loan.financing'
    _description = 'Loan Microfinancing'
    _order = 'write_date desc'

    code = fields.Char(readonly=True)
    status = fields.Selection([('active','Active'),('archive','Archived')], default='archive')
    cosigner_id = fields.Many2one(comodel_name='res.partner', string='Cosigner')
    date_created = fields.Datetime(default=fields.Datetime.now())
    branch_id = fields.Many2one('res.branch','Branch')


class ResBranch(models.Model):
    _name = 'res.branch'

    name = fields.Char(readonly=True)
    company_id = fields.Many2one('res.company', 'Related Company', readonly=True)
    related_partner = fields.Many2one(related='company_id.partner_id', readonly=True)
    index = fields.Integer()
    code = fields.Char('Code')
    financing_ids = fields.One2many('credit.loan.financing','branch_id','Loan Accounts')
    area_ids = fields.One2many('res.area','branch_id','Area')
    manager_id = fields.One2many('res.partner','branch_id','Branch Manager',domain=[('type','=','bm')])
    manager = fields.Char(related='manager_id.name', string='Branch Manager')
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char()
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    email = fields.Char(related='manager_id.email', store=True, readonly=False)
    phone = fields.Char(related='manager_id.phone', store=True, readonly=False)
    website = fields.Char()
    vat = fields.Char(string="Tax ID", readonly=False)

    @api.model
    def create(self, values):
        if values.get('partner_id'):
            self.clear_caches()
            return super(ResBranch, self).create(values)
        values['index'] = int(self.search([], order='index desc',limit=1).index)+1
        values['name'] = '%s - %s' % (values.get('code'), "{0:0=2d}".format(values.get('index')))
        company = self.env['res.company'].create({
            'name': values.get('name'),
            'email': values.get('email'),
            'phone': values.get('phone'),
            'website': values.get('website'),
            'vat': values.get('vat')
        })

        values['company_id'] = company.id

        return super(ResBranch, self).create(values)


class ResArea(models.Model):
    _name = 'res.area'

    name = fields.Char(compute='_get_name')
    code = fields.Char(related='officer_id.short_code', store=True, readonly=True)
    branch_id = fields.Many2one('res.branch','Branch', store=True)
    group_ids = fields.One2many('credit.loan.group','area_id','Groups')
    officer_id = fields.One2many('res.partner','area_id','Assigned DO', domain=[('type','=','do')])
    officer = fields.Char(related='officer_id.name', string='Assigned DO')
    city = fields.Char(related='branch_id.city',string='City', store=True)
    street2 = fields.Char()

    @api.depends('street2','code')
    def _get_name(self):
        for rec in self:
            rec.name = '%s - %s' % (rec.code,rec.street2)


