# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import tools, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
# class CreditPayment(models.Model):
#     _name = 'credit.loan.payment'


# class CreditCollection(models.Model):
#     _name = 'credit.loan.collection'
#
#     name = fields.Char()
#     collection_line = fields.One2many('credit.loan.collection', 'amortization_id', 'Collections')
#     application_id = fields.Many2one('crm.lead', 'Application Seq.')

class SalesOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _create_invoice(self, context):
        date_invoice = context['date_invoice']
        date_invoice = date_invoice
        date_due = context['date_due']
        date_due = date_due
        amount = context['amount']
        inv_obj = self.env['account.invoice']
        ir_property_obj = self.env['ir.property']

        account_id = False
        if self.opportunity_id.product_id.id:
            account_id = self.fiscal_position_id.map_account(
                self.opportunity_id.product_id.property_account_income_id or self.opportunity_id.product_id.categ_id.property_account_income_categ_id).id
        if not account_id:
            inc_acc = ir_property_obj.get('property_account_income_categ_id', 'product.category')
            account_id = self.fiscal_position_id.map_account(inc_acc).id if inc_acc else False
        if not account_id:
            raise UserError(
                _(
                    'There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                (self.opportunity_id.product_id.name,))

        # if self.amount <= 0.00:
        #     raise UserError(_('The value of the down payment amount must be positive.'))
        context = {'lang': self.partner_id.lang}
        # if self.advance_payment_method == 'percentage':
        #     amount = order.amount_untaxed * self.amount / 100
        #     name = _("Down payment of %s%%") % (self.amount,)
        # else:
        #     amount = self.amount
        name = _('Down Payment')
        del context
        taxes = self.opportunity_id.product_id.taxes_id.filtered(lambda r: not self.company_id or r.company_id == self.company_id)
        if self.fiscal_position_id and taxes:
            tax_ids = self.fiscal_position_id.map_tax(taxes, self.opportunity_id.product_id, self.partner_shipping_id).ids
        else:
            tax_ids = taxes.ids

        invoice = inv_obj.create({
            'name': self.client_order_ref or self.name,
            'origin': self.name,
            'type': 'out_invoice',
            'reference': False,
            'account_id': self.partner_id.property_account_receivable_id.id,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': name,
                'origin': self.name,
                'account_id': account_id,
                'price_unit': amount,
                'quantity': 1.0,
                'discount': 0.0,
                'uom_id': self.opportunity_id.product_id.uom_id.id,
                'product_id': self.opportunity_id.product_id.id,
                # 'sale_line_ids': [(6, 0, [so_line.id])],
                'invoice_line_tax_ids': [(6, 0, tax_ids)],
                # 'analytic_tag_ids': [(6, 0, so_line.analytic_tag_ids.ids)],
                'account_analytic_id': self.analytic_account_id.id or False,
            })],
            'currency_id': self.pricelist_id.currency_id.id,
            'payment_term_id': self.payment_term_id.id,
            'fiscal_position_id': self.fiscal_position_id.id or self.partner_id.property_account_position_id.id,
            'team_id': self.team_id.id,
            'user_id': self.user_id.id,
            'company_id': self.company_id.id,
            'comment': self.note,
            'date_invoice':date_invoice,
            'date_due':date_due
        })
        invoice.compute_taxes()
        invoice.message_post_with_view('mail.message_origin_link',
                                       values={'self': invoice, 'origin': self},
                                       subtype_id=self.env.ref('mail.mt_note').id)
        return invoice

class CreditCollectionLine(models.Model):
    _name = 'credit.loan.collection.line'

    name = fields.Char()
    collection_id = fields.Many2one('credit.loan.collection', 'Collection')
    order_id = fields.Many2one('sale.order', 'Sales Order', related='collection_id.order_id')
    # order_line_id = fields.Many2one('sale.order.line', 'Related Document')
    invoice_id = fields.Many2one('account.invoice', 'Related Document')
    date_created = fields.Datetime('Date Created', default=fields.Datetime.now())
    currency_id = fields.Many2one('res.currency', related='collection_id.currency_id')
    status = fields.Selection([('draft', 'Draft'),
                               ('active', 'Active'),
                               ('paid', 'Paid'),
                               ('cancel','Cancelled')])
    date = fields.Date()
    principal = fields.Monetary('Principal')
    amortization = fields.Monetary('Amortization')
    interest = fields.Monetary('Interest')
    surcharge = fields.Monetary('Surcharge')
    penalty = fields.Monetary('Penalty')

class CreditCollection(models.Model):
    _name = 'credit.loan.collection'

    name = fields.Char()
    application_id = fields.Many2one('crm.lead', 'Application Seq.')
    order_id = fields.Many2one('sale.order', 'Sales Order')
    date_created = fields.Datetime('Date Created', default=fields.Datetime.now())
    collection_line_ids = fields.One2many('credit.loan.collection.line','collection_id','Collection Line')
    product_id = fields.Many2one('product.template', related='application_id.product_id', string='Applied Product')
    currency_id = fields.Many2one('res.currency', related='product_id.currency_id')
    term_id = fields.Many2one('account.payment.term', related='product_id.payment_term')
    interest_id = fields.Many2one('credit.loan.interest', related='product_id.interest_id')
    interest = fields.Monetary(compute='_compute_amortization')
    surcharge_id = fields.Many2one('credit.loan.surcharge', related='product_id.surcharge_id')
    surcharge = fields.Monetary(compute='_compute_amortization')
    penalty_id = fields.Many2one('credit.loan.penalty', related='product_id.penalty_id')
    penalty = fields.Monetary(compute='_compute_amortization')
    collateral_id = fields.Many2one('credit.loan.collateral', related='product_id.collateral_id')
    fund_id = fields.Many2one('credit.loan.fund', related='product_id.fund_id')
    principal = fields.Monetary(compute='_compute_amortization')
    amortization = fields.Monetary(compute='_compute_amortization')
    status = fields.Selection([('draft', 'Draft'),
                               ('active', 'Active'),
                               ('complete', 'Complete')])

    @api.depends('interest_id','surcharge_id','penalty_id', 'application_id', 'product_id')
    def _compute_amortization(self):
        for rec in self:

            term = int(sum([line.days/30 for line in rec.product_id.payment_term.line_ids if line.value == 'balance']))
            print(term)
            if rec.product_id.loanclass == 'individual':
                loan_amount = rec.application_id.loan_amount
                principal = loan_amount/term
            elif rec.product_id.loanclass == 'group':
                loan_amount = rec.application_id.group_id.loan_amount
                principal = (loan_amount/term)/rec.application_id.member_count
            rec.interest = (principal * rec.interest_id.rate) + rec.interest_id.amount
            rec.surcharge = (principal * rec.surcharge_id.rate) + rec.surcharge_id.amount
            rec.penalty = (principal * rec.penalty_id.rate) + rec.penalty_id.amount
            rec.principal = principal
            rec.amortization = (principal+rec.interest) - rec.surcharge

    @api.model
    def create(self, values):
        application = self.env['crm.lead'].sudo().search([('id','=',values['application_id'])])
        collection = super(CreditCollection, self).create(values)
        print(collection)
        order = application.order_ids.search([('opportunity_id','=',application.id)], limit=1)
        if not order:
            # if first SO: add processing fee
            order = self.env['sale.order'].sudo().create({
                'opportunity_id': application.id,
                'partner_id': application.partner_id.id,
                'partner_invoice_id': application.partner_id.id,
                'partner_shipping_id': application.partner_id.id,
                'pricelist_id': self.env['product.pricelist'].search([], limit=1).id,
                'company_id':application.branch_id.company_id.id,
            })

            self.env['sale.order.line'].sudo().create({
                'order_id':order.id,
                'name':self.env['product.template'].sudo().search([('name','=','Processing Fee')]).name,
                'product_id': self.env['product.template'].sudo().search([('name', '=', 'Processing Fee')]).id,
                'price_unit': self.env['product.template'].sudo().search([('name', '=', 'Processing Fee')]).standard_price
            })

        for line in range(0,int(sum([line.days/30 for line in application.product_id.payment_term.line_ids if line.value == 'balance']))):
            try:
                self.env['sale.order.line'].sudo().create({
                    'order_id': order.id,
                    'name': order.opportunity_id.product_id.name,
                    'product_id': order.opportunity_id.product_id.id,
                    'price_unit': collection.amortization
                })

                print('CREATING COLLECTION LINES...', line)

                self.env['credit.loan.collection.line'].sudo().create({
                    'collection_id':collection.id,
                    'status':'draft',
                    'principal':collection.principal,
                    'amortization':collection.amortization,
                    'interest':collection.interest,
                    'surcharge':collection.surcharge,
                    'penalty':collection.penalty
                })

                print('COLLECTION DONE!')
            except Exception as e:
                raise UserError(_(str(e)))

        collection.order_id = order
        order.action_confirm()
        return collection

class LoanApplication(models.Model):
    _inherit = 'crm.lead'

    status = fields.Selection(string='Status', selection_add=[('disburse', 'Disbursement'), ('collection', 'Collection')], required=True, track_visibility='onchange')
    collection_ids = fields.One2many('credit.loan.collection', 'application_id', 'Loan Collection')
    collection_line_ids = fields.One2many('credit.loan.collection.line', related='collection_ids.collection_line_ids')
    date_approved = fields.Datetime('Date Approved')
    date_released = fields.Datetime('Date Released')

    @api.multi
    def approve_application(self):
        try:
            if self.stage_id.id != self.env['crm.stage'].sudo().search([('name', '=', 'Proposition')]).id:
                raise UserError(_("The application must be endorsed first!"))
                # TODO: create collection for individual loans
            if self.product_id.loanclass == 'group':
                for application in self.group_id.application_ids:
                    print('CREATING COLLECTION FOR:', application.partner_id.name)
                    self.env['credit.loan.collection'].sudo().create({
                        'application_id': application.id,
                        'status': 'draft',
                    })
                    application.write({
                        'stage_id': self.env['crm.stage'].search([('name', '=', 'Approved')]).id,
                        'status': 'disburse'
                    })
                print('COLLECTION FOR GROUP MEMBERS CREATED!')
                return True

            elif self.product_id.loanclass == 'individual':

                print('CREATING COLLECTION FOR:', self.partner_id.name)
                self.env['credit.loan.collection'].sudo().create({
                    'application_id': self.id,
                    'status': 'draft',
                })
                self.write({
                    'stage_id': self.env['crm.stage'].search([('name', '=', 'Approved')]).id,
                    'status': 'disburse'
                })
                print('COLLECTION FOR APPLICANT CREATED!')
                return True
        except Exception as e:
            raise UserError(_(str(e)))


class Holidays(models.Model):
    _name = 'credit.loan.collection.holiday'

    name = fields.Char(string='Holiday', required=True)
    description = fields.Text(string='Description')
    type = fields.Selection([('regular', 'Regular Holiday'),
                             ('special_nw', 'Special Non-working Holiday'),
                             ('special_w', 'Special Working Holiday')], string='Holiday Type', required=True)
    month = fields.Selection([('1', 'January'),
                              ('2', 'February'),
                              ('3', 'March'),
                              ('4', 'April'),
                              ('5', 'May'),
                              ('6', 'June'),
                              ('7', 'July'),
                              ('8', 'August'),
                              ('9', 'September'),
                              ('10', 'October'),
                              ('11', 'November'),
                              ('12', 'December')], string='Month', required=True)
    day = fields.Selection([(str(i), str(i).zfill(2)) for i in range(1, 32)], string='Day', required=True)
