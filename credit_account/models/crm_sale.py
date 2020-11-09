# -*- coding: utf-8 -*-

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import date, datetime
from odoo.modules.module import get_module_resource
from odoo import tools, _
from odoo.exceptions import UserError, ValidationError

class Lead(models.Model):
    _inherit = 'crm.lead'

    @api.multi
    def action_manage_group(self, context=None):
        try:
            print(context['default_application_id'])
            return {
                'type':'ir.actions.act_window',
                'res_model':'credit.loan.group',
                'view_type':'form',
                'view_mode':'form',
                'res_id':self.env['credit.loan.group'].search([('id','=',context['default_application_id'])]).id,
                'target':'new'
            }
        except Exception as e:
            raise(_("ERROR: 'action_manage_group' "+str(e)))

    @api.model
    def create(self, vals):
        try:
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



            partner_id = self.env['credit.loan.financing'].search([('id','=',vals.get('financing_id'))]).member_id
            vals['index'] = int(self.search([], order='index desc', limit=1).index) + 1
            vals['code'] = '%s - %s' % (self.env['credit.loan.financing'].search([('id','=',vals.get('financing_id'))]).code,
                                               "{0:0=3d}".format(vals.get('index')))
            vals['name'] = '%s - %s'% (vals['code'], partner_id.name)
            onchange_values = self._onchange_partner_id_values(partner_id.id)
            onchange_values.update(vals)  # we don't want to overwrite any existing key
            vals = onchange_values
            lead = super(Lead, self).create(vals)
            sale_order = self.env['sale.order'].search([('opportunity_id','=',lead.id)], limit=1)
            print('SO', sale_order)
            print('ID', lead.id)
            print(partner_id.id)
            if not sale_order:
                order = self.env['sale.order'].create({
                    'opportunity_id': lead.id,
                    'partner_id': partner_id.id,
                    'partner_invoice_id': partner_id.id,
                    'partner_shipping_id': partner_id.id,
                    'pricelist_id': self.env['product.pricelist'].search([],limit=1).id
                })
                for product in lead.product_id.child_ids:
                    print('Lead Product ID', lead.product_id.id)
                    print('Parent ID', product.package_id.id)
                    print('Product ID', product.id)
                    print('class', product.package_id.loanclass)
                    # if not lead.group_id and product.package_id.loanclass == 'group':
                    product = self.env['product.product'].search([('product_tmpl_id','=',product.id)])
                    self.env['sale.order.line'].create({
                        'order_id': order.id,
                        'name': product.name,
                        'product_id': product.id
                    })
            # context: no_log, because subtype already handle this
            return lead
        except Exception as e:
            raise UserError(_(str(e)))

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



