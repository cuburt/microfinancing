# -*- coding: utf-8 -*-

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import date, datetime
from odoo.modules.module import get_module_resource
from odoo import tools, _
from odoo.exceptions import UserError, ValidationError

class Lead(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def create(self, vals):
        if vals.get('website'):
            vals['website'] = self.env['res.partner']._clean_website(vals['website'])
        # set up context used to find the lead's sales channel which is needed
        # to correctly set the default stage_id
        context = dict(self._context or {})
        if vals.get('type') and not self._context.get('default_type'):
            context['default_type'] = vals.get('type')
        if vals.get('team_id') and not self._context.get('default_team_id'):
            context['default_team_id'] = vals.get('team_id')

        if vals.get('user_id') and 'date_open' not in vals:
            vals['date_open'] = fields.Datetime.now()



        partner_id = vals.get('partner_id') or context.get('default_partner_id')
        onchange_values = self._onchange_partner_id_values(partner_id)
        onchange_values.update(vals)  # we don't want to overwrite any existing key
        vals = onchange_values
        lead = super(Lead, self.with_context(context, mail_create_nolog=True)).create(vals)
        sale_order = self.env['sale.order'].search([('opportunity_id','=',lead.id)], limit=1)
        print('SO', sale_order)
        print('ID', lead.id)
        if not sale_order:
            order = self.env['sale.order'].create({
                'opportunity_id': lead.id,
                'partner_id': partner_id,
                'partner_invoice_id': partner_id,
                'partner_shipping_id': partner_id,
                'pricelist_id': self.env['product.pricelist'].search([],limit=1).id
            })
            self.env['sale.order.line'].create({
                'order_id': order.id,
                'name': lead.product_id.name,
                'product_id': lead.product_id.id
        })
        # context: no_log, because subtype already handle this
        return lead

# class SaleOrder(models.Model):
#     _inherit = 'sale.order'
#     @api.model
#     def create(self, vals):
#         if vals.get('name', _('New')) == _('New'):
#             if 'company_id' in vals:
#                 vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
#                     'sale.order') or _('New')
#             else:
#                 vals['name'] = self.env['ir.sequence'].next_by_code('sale.order') or _('New')
#
#         # Makes sure partner_invoice_id', 'partner_shipping_id' and 'pricelist_id' are defined
#         if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id', 'pricelist_id']):
#             partner = self.env['res.partner'].browse(vals.get('partner_id'))
#             addr = partner.address_get(['delivery', 'invoice'])
#             vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
#             vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])
#             vals['pricelist_id'] = vals.setdefault('pricelist_id',
#                                                    partner.property_product_pricelist and partner.property_product_pricelist.id)
#
#
#         result = super(SaleOrder, self).create(vals)
#         return result
#
#
# if not self.env['sale.order'].search(
#         [('opportunity_id', '=', self.env['crm.lead'].search([('application_id', '=', self.id)], limit=1).id),
#          ('opportunity_id.application_id', '=', self.id)], limit=1):
#     self.env['sale.order'].create({
#         'opportunity_id': self.env['crm.lead'].search([('application_id', '=', self.id)], limit=1).id
#     })
#
# return super(LoanApplication, self).write(values)



