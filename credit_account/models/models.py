# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import tools, _
from odoo.exceptions import ValidationError, UserError

class Branch(models.Model):
    _inherit = 'res.branch'

    @api.model
    def create(self, values):
        try:
            if values.get('related_partner'):
                self.clear_caches()
                return super(Branch, self).create(values)
            values['index'] = int(self.search([], order='index desc',limit=1).index)+1
            values['name'] = '%s-%s' % (values.get('code'), "{0:0=2d}".format(values.get('index')))
            parent = self.env['res.company'].search([('name','=','CARE Foundation Inc.')])
            if not parent:
                raise UserError(_("Please create a company named 'CARE Foundation Inc.' first."))
            company = self.env['res.company'].create({
                'parent_id':parent.id,
                'name': values.get('name'),
                'email': values.get('email'),
                'phone': values.get('phone'),
                'website': values.get('website'),
                'vat': values.get('vat'),
            })

            # property = self.env['ir.property'].sudo().create({
            #     'name':'property_account_receivable_id',

            # })
            try:
                for account in self.env['account.account'].sudo().search([('company_id.id','=',parent.id)]):
                    self.env['account.account'].sudo().create({
                        'code':account.code,
                        'name':account.name,
                        'user_type_id':account.user_type_id.id,
                        'company_id':company.id,
                        'reconcile':True
                    })
            #
            #     try:
            #         company.partner_id.property_account_receivable_id = self.env['account.account'].sudo().search(
            #             [('internal_type', '=', 'receivable'), ('deprecated', '=', False),
            #              ('company_id.id', '=', company.id), ('code', '=', '11710')])
            #         company.partner_id.property_account_payable_id = self.env['account.account'].sudo().search(
            #             [('internal_type', '=', 'payable'), ('deprecated', '=', False),
            #              ('company_id.id', '=', company.id), ('code', '=', '00000')])
            #     except:
            #         raise UserError(_('Set accounting entries for main company first.'))
            #
            except Exception as e:
                raise ValidationError(_("A problem was encountered while migrating chart of accounts. Please contact site administrator immediately. ERROR: 'create' : "+str(e)))

            try:

                # UNPAID PURCHASE | PAYMENT ON CREDIT | DEBIT:OTHER ASSETS(EQUIPMENT), CREDIT:LIABILITIES(PAYABLE)
                purchase_credit = self.env['account.journal'].sudo().create({
                    'name': company.name + ' Purchase Credit Journal',
                    'type': 'purchase',
                    'code': 'LBT',
                    'company_id': company.id,
                    # 'default_debit_account_id':
                    # 'default_credit_account_id':
                })
                print(purchase_credit.name + ' created for company ' + company.name)

                # PAID PURCHASE | PAYMENT ON CASH | LOAN DISBURSEMENT | CASH OUTFLOW | DEBIT:EXPENSE|ASSETS(EQUIPMENT/RECEIVABLES)|LIABILITIES(PAYABLE), CREDIT: ASSET(CASH/BANK)
                cash_payment = self.env['account.journal'].sudo().create({
                    'name': company.name + ' Cash Payment Journal',
                    'type': 'purchase',
                    'code': 'EXP',
                    'company_id': company.id,
                    # 'default_debit_account_id':
                    # 'default_credit_account_id':
                })
                print(cash_payment.name + ' created for company ' + company.name)

                # FOR UNPAID LOANS | RECEIPT ON CREDIT | LOAN COLLECTION | CASH INFLOW | DEBIT:ASSET(RECEIVABLE), CREDIT:REVENUE
                receipt_credit = self.env['account.journal'].sudo().create({
                    'name': company.name + ' Receivable Journal',
                    'type': 'sale',
                    'code': 'RCV',
                    'company_id': company.id,
                    # 'default_debit_account_id':
                    # 'default_credit_account_id':
                })
                print(receipt_credit.name + ' created for company ' + company.name)

                # FOR PAID LOANS | RECEIPT ON CASH | LOAN COLLECTION | CASH INFLOW | DEBIT:ASSET(CASH/BANK), CREDIT:ASSET(RECEIVABLE)
                bank_loan_collection = self.env['account.journal'].sudo().create({
                    'name': company.name + ' Cheque Receipt Journal',
                    'type': 'bank',
                    'code': 'BNK',
                    'company_id': company.id
                    # 'default_debit_account_id':
                    # 'default_credit_account_id':
                })
                print(bank_loan_collection.name + ' created for company ' + company.name)
                cash_loan_collection = self.env['account.journal'].sudo().create({
                    'name': company.name + ' Cash Receipt Journal',
                    'type': 'cash',
                    'code': 'CSH',
                    'company_id': company.id
                    # 'default_debit_account_id':
                    # 'default_credit_account_id':
                })
                print(cash_loan_collection.name+' created for company '+company.name)

                general_journal = self.env['account.journal'].sudo().create({
                    'name':  company.name + ' General Journal',
                    'type': 'general',
                    'code': 'GJ',
                    'company_id': company.id
                    # 'default_debit_account_id':
                    # 'default_credit_account_id':
                })
                print(general_journal.name + ' created for company ' + company.name)
            except Exception as e:
                raise ValidationError(_("A problem was encountered while migrating account journals. Please contact site administrator immediately. ERROR: 'create' : "+str(e)))

            values['company_id'] = company.id

#================================= FOR RELATED PARTNER =================================================================
            try:
                property_account_receivable = self.env['account.account'].sudo().search(
                    [('company_id.id', '=', company.id), ('deprecated', '=', False),
                     ('internal_type', '=', 'receivable'),
                     ('code', '=', '11710')])
                property_account_payable = self.env['account.account'].sudo().search(
                    [('company_id.id', '=', company.id), ('deprecated', '=', False),
                     ('internal_type', '=', 'payable'),
                     ('code', '=', '00000')])
                print(property_account_receivable.id)
                print(property_account_payable.id)
                company.partner_id.sudo().write({
                    'property_account_receivable_id': property_account_receivable.id,
                    'property_account_payable_id': property_account_payable.id
                })

                property_account_receivable_id = self.env['ir.model.fields'].search(
                    [('model', '=', 'res.partner'), ('name', '=', 'property_account_receivable_id')])
                main_property_account_receivable_id = self.env['ir.property'].sudo().search([('name','=','property_account_receivable_id'),
                                                                                             ('value_reference','=','account.account,%s' % property_account_receivable.id),
                                                                                             ('fields_id','=',property_account_receivable_id.id),
                                                                                             ('company_id.id','!=',company.id)])
                if main_property_account_receivable_id:
                    main_property_account_receivable_id.sudo().write({
                        'name': 'property_account_receivable_id',
                        'company_id': company.id,
                        'value_reference': 'account.account,%s' % property_account_receivable.id,
                        'fields_id': property_account_receivable_id.id,
                        'type': 'many2one'
                    })
                else:
                    self.env['ir.property'].create({
                        'name': 'property_account_receivable_id',
                        'company_id': company.id,
                        'value_reference': 'account.account,%s' % property_account_receivable.id,
                        'fields_id': property_account_receivable_id.id,
                        'type':'many2one'
                    })

                property_account_payable_id = self.env['ir.model.fields'].search(
                    [('model', '=', 'res.partner'), ('name', '=', 'property_account_payable_id')])
                main_property_account_payable_id = self.env['ir.property'].sudo().search(
                    [('name', '=', 'property_account_payable_id'),
                     ('value_reference', '=', 'account.account,%s' % property_account_payable.id),
                     ('fields_id', '=', property_account_payable_id.id),
                     ('company_id.id', '!=', company.id)])
                if main_property_account_payable_id:
                    main_property_account_payable_id.sudo().write({
                        'name': 'property_account_payable_id',
                        'company_id': company.id,
                        'value_reference': 'account.account,%s' % property_account_payable.id,
                        'fields_id': property_account_payable_id.id,
                        'type': 'many2one'
                    })
                else:
                    self.env['ir.property'].create({
                        'name': 'property_account_payable_id',
                        'company_id': company.id,
                        'value_reference': 'account.account,%s' % property_account_payable.id,
                        'fields_id': property_account_payable_id.id,
                        'type': 'many2one'
                    })
            except Exception as e:
                raise ValidationError(_(str(e)))
            print(company)

#============================================= FOR PRODUCT CATEGORY ====================================================
            try:

                for category in self.env['product.category'].sudo().search([]):
                    property_account_receivable = self.env['account.account'].sudo().search(
                            [('company_id.id', '=', company.id), ('deprecated', '=', False),
                             ('internal_type', '=', 'receivable'),
                             ('code', '=', '11780')])
                    property_account_payable = self.env['account.account'].sudo().search(
                            [('company_id.id', '=', company.id), ('deprecated', '=', False),
                             ('internal_type', '=', 'payable'),
                             ('code', '=', '00000')])
                    property_account_income = self.env['account.account'].sudo().search(
                            [('company_id.id', '=', company.id), ('deprecated', '=', False),
                             ('internal_type', '=', 'other'),
                             ('code', '=', '40400')])
                    property_account_expense = self.env['account.account'].sudo().search(
                            [('company_id.id', '=', company.id), ('deprecated', '=', False),
                             ('internal_type', '=', 'other'),
                             ('code', '=', '73520')])
#======================================= LOAN PRODUCT ======================================================
                    if category.name == 'Loan Products':
                        #ACCOUNT OBJECTS
                        property_account_receivable = self.env['account.account'].sudo().search(
                            [('company_id.id', '=', company.id), ('deprecated', '=', False),
                             ('internal_type', '=', 'receivable'),
                             ('code', '=', '11710')])
                        property_account_payable = self.env['account.account'].sudo().search(
                            [('company_id.id', '=', company.id), ('deprecated', '=', False),
                             ('internal_type', '=', 'payable'),
                             ('code', '=', '00000')])
                        property_account_income = self.env['account.account'].sudo().search(
                            [('company_id.id', '=', company.id), ('deprecated', '=', False),
                             ('internal_type', '=', 'other'),
                             ('code', '=', '40400')])
                        property_account_expense = self.env['account.account'].sudo().search(
                            [('company_id.id', '=', company.id), ('deprecated', '=', False),
                             ('internal_type', '=', 'other'),
                             ('code', '=', '73211')])
                        # UPDATE IF EXISTS ELSE CREATE
                    elif category.name == 'Fees':
                        # ACCOUNT OBJECTS
                        property_account_receivable = self.env['account.account'].sudo().search(
                            [('company_id.id', '=', company.id), ('deprecated', '=', False),
                             ('internal_type', '=', 'receivable'),
                             ('code', '=', '11780')])
                        property_account_payable = self.env['account.account'].sudo().search(
                            [('company_id.id', '=', company.id), ('deprecated', '=', False),
                             ('internal_type', '=', 'payable'),
                             ('code', '=', '00000')])
                        property_account_income = self.env['account.account'].sudo().search(
                            [('company_id.id', '=', company.id), ('deprecated', '=', False),
                             ('internal_type', '=', 'other'),
                             ('code', '=', '40135')])
                        property_account_expense = self.env['account.account'].sudo().search(
                            [('company_id.id', '=', company.id), ('deprecated', '=', False),
                             ('internal_type', '=', 'other'),
                             ('code', '=', '73211')])

                    elif category.name == 'Insurance':
                        # ACCOUNT OBJECTS
                        property_account_receivable = self.env['account.account'].sudo().search(
                            [('company_id.id', '=', company.id), ('deprecated', '=', False),
                             ('internal_type', '=', 'receivable'),
                             ('code', '=', '11780')])
                        property_account_payable = self.env['account.account'].sudo().search(
                            [('company_id.id', '=', company.id), ('deprecated', '=', False),
                             ('internal_type', '=', 'payable'),
                             ('code', '=', '00000')])
                        property_account_income = self.env['account.account'].sudo().search(
                            [('company_id.id', '=', company.id), ('deprecated', '=', False),
                             ('internal_type', '=', 'other'),
                             ('code', '=', '40160')])
                        property_account_expense = self.env['account.account'].sudo().search(
                            [('company_id.id', '=', company.id), ('deprecated', '=', False),
                             ('internal_type', '=', 'other'),
                             ('code', '=', '73430')])

                    #ACCOUNT FIELDS
                    property_account_receivable_categ_id = self.env['ir.model.fields'].search(
                        [('model', '=', 'product.category'), ('name', '=', 'property_account_receivable_categ_id')])
                    property_account_payable_categ_id = self.env['ir.model.fields'].search(
                        [('model', '=', 'product.category'), ('name', '=', 'property_account_payable_categ_id')])
                    property_account_income_categ_id = self.env['ir.model.fields'].search(
                        [('model', '=', 'product.category'), ('name', '=', 'property_account_income_categ_id')])
                    property_account_expense_categ_id = self.env['ir.model.fields'].search(
                        [('model', '=', 'product.category'), ('name', '=', 'property_account_expense_categ_id')])
                    # EXISTING ACCOUNTS
                    main_property_account_receivable_categ_id = self.env['ir.property'].sudo().search(
                        [('name', '=', 'property_account_receivable_categ_id'),
                         ('value_reference', '=', 'account.account,%s' % property_account_receivable.id),
                         ('fields_id', '=', property_account_receivable_categ_id.id),
                         ('company_id.id', '!=', company.id)])

                    main_property_account_payable_categ_id = self.env['ir.property'].sudo().search(
                        [('name', '=', 'property_account_payable_categ_id'),
                         ('value_reference', '=', 'account.account,%s' % property_account_payable.id),
                         ('fields_id', '=', property_account_payable_categ_id.id),
                         ('company_id.id', '!=', company.id)])

                    main_property_account_income_categ_id = self.env['ir.property'].sudo().search(
                        [('name', '=', 'property_account_income_categ_id'),
                         ('value_reference', '=', 'account.account,%s' % property_account_payable.id),
                         ('fields_id', '=', property_account_income_categ_id.id),
                         ('company_id.id', '!=', company.id)])

                    main_property_account_expense_categ_id = self.env['ir.property'].sudo().search(
                        [('name', '=', 'property_account_expense_categ_id'),
                         ('value_reference', '=', 'account.account,%s' % property_account_payable.id),
                         ('fields_id', '=', property_account_expense_categ_id.id),
                         ('company_id.id', '!=', company.id)])

                    if main_property_account_receivable_categ_id:
                        main_property_account_receivable_categ_id.sudo().write({
                            'name': 'property_account_receivable_categ_id',
                            'company_id': company.id,
                            'value_reference': 'account.account,%s' % property_account_receivable.id,
                            'res_id': 'product.category,%s' % category.id,
                            'fields_id': property_account_receivable_categ_id.id,
                            'type': 'many2one'
                        })
                    else:
                        self.env['ir.property'].create({
                            'name': 'property_account_receivable_categ_id',
                            'company_id': company.id,
                            'value_reference': 'account.account,%s' % property_account_receivable.id,
                            'res_id': 'product.category,%s' % category.id,
                            'fields_id': property_account_receivable_categ_id.id,
                            'type': 'many2one'
                        })

                    if main_property_account_payable_categ_id:
                        main_property_account_payable_categ_id.sudo().write({
                            'name': 'property_account_payable_categ_id',
                            'company_id': company.id,
                            'value_reference': 'account.account,%s' % property_account_payable.id,
                            'res_id': 'product.category,%s' % category.id,
                            'fields_id': property_account_payable_categ_id.id,
                            'type': 'many2one'
                        })
                    else:
                        self.env['ir.property'].create({
                            'name': 'property_account_payable_categ_id',
                            'company_id': company.id,
                            'value_reference': 'account.account,%s' % property_account_payable.id,
                            'res_id': 'product.category,%s' % category.id,
                            'fields_id': property_account_payable_categ_id.id,
                            'type': 'many2one'
                        })

                    if main_property_account_income_categ_id:
                        main_property_account_income_categ_id.sudo().write({
                            'name': 'property_account_income_categ_id',
                            'company_id': company.id,
                            'value_reference': 'account.account,%s' % property_account_income.id,
                            'res_id': 'product.category,%s' % category.id,
                            'fields_id': property_account_income_categ_id.id,
                            'type': 'many2one'
                        })
                    else:
                        self.env['ir.property'].create({
                            'name': 'property_account_income_categ_id',
                            'company_id': company.id,
                            'value_reference': 'account.account,%s' % property_account_income.id,
                            'res_id': 'product.category,%s' % category.id,
                            'fields_id': property_account_income_categ_id.id,
                            'type': 'many2one'
                        })

                    if main_property_account_expense_categ_id:
                        main_property_account_expense_categ_id.sudo().write({
                            'name': 'property_account_expense_categ_id',
                            'company_id': company.id,
                            'value_reference': 'account.account,%s' % property_account_expense.id,
                            'res_id': 'product.category,%s' % category.id,
                            'fields_id': property_account_expense_categ_id.id,
                            'type': 'many2one'
                        })
                    else:
                        self.env['ir.property'].create({
                            'name': 'property_account_expense_categ_id',
                            'company_id': company.id,
                            'value_reference': 'account.account,%s' % property_account_expense.id,
                            'res_id': 'product.category,%s' % category.id,
                            'fields_id': property_account_expense_categ_id.id,
                            'type': 'many2one'
                        })
                for interest in self.env['credit.loan.interest'].sudo().search([]):
                    property_account_receivable = self.env['account.account'].sudo().search(
                        [('company_id.id', '=', company.id), ('deprecated', '=', False),
                         ('internal_type', '=', 'receivable'),
                         ('code', '=', '11720')])
                    property_account_payable = self.env['account.account'].sudo().search(
                        [('company_id.id', '=', company.id), ('deprecated', '=', False),
                         ('internal_type', '=', 'payable'),
                         ('code', '=', '00000')])
                    property_account_income = self.env['account.account'].sudo().search(
                        [('company_id.id', '=', company.id), ('deprecated', '=', False),
                         ('internal_type', '=', 'other'),
                         ('code', '=', '40110')])
                    property_account_expense = self.env['account.account'].sudo().search(
                        [('company_id.id', '=', company.id), ('deprecated', '=', False),
                         ('internal_type', '=', 'other'),
                         ('code', '=', '71100')])

                    property_account_receivable_id = self.env['ir.model.fields'].search(
                        [('model', '=', 'credit.loan.interest'), ('name', '=', 'property_account_receivable_id')])
                    property_account_payable_id = self.env['ir.model.fields'].search(
                        [('model', '=', 'credit.loan.interest'), ('name', '=', 'property_account_payable_id')])
                    property_account_income_id = self.env['ir.model.fields'].search(
                        [('model', '=', 'credit.loan.interest'), ('name', '=', 'property_account_income_id')])
                    property_account_expense_id = self.env['ir.model.fields'].search(
                        [('model', '=', 'credit.loan.interest'), ('name', '=', 'property_account_expense_id')])

                    main_property_account_receivable_id = self.env['ir.property'].sudo().search(
                        [('name', '=', 'property_account_receivable_id'),
                         ('value_reference', '=', 'account.account,%s' % property_account_receivable.id),
                         ('fields_id', '=', property_account_receivable_id.id),
                         ('company_id.id', '!=', company.id)])

                    main_property_account_payable_id = self.env['ir.property'].sudo().search(
                        [('name', '=', 'property_account_payable_id'),
                         ('value_reference', '=', 'account.account,%s' % property_account_payable.id),
                         ('fields_id', '=', property_account_payable_id.id),
                         ('company_id.id', '!=', company.id)])

                    main_property_account_income_id = self.env['ir.property'].sudo().search(
                        [('name', '=', 'property_account_income_id'),
                         ('value_reference', '=', 'account.account,%s' % property_account_payable.id),
                         ('fields_id', '=', property_account_income_id.id),
                         ('company_id.id', '!=', company.id)])

                    main_property_account_expense_id = self.env['ir.property'].sudo().search(
                        [('name', '=', 'property_account_expense_id'),
                         ('value_reference', '=', 'account.account,%s' % property_account_payable.id),
                         ('fields_id', '=', property_account_expense_id.id),
                         ('company_id.id', '!=', company.id)])

                    if main_property_account_receivable_id:
                        main_property_account_receivable_id.sudo().write({
                            'name': 'property_account_receivable_id',
                            'company_id': company.id,
                            'value_reference': 'account.account,%s' % property_account_receivable.id,
                            'res_id': 'credit.loan.interest,%s' % interest.id,
                            'fields_id': property_account_receivable_id.id,
                            'type': 'many2one'
                        })
                    else:
                        self.env['ir.property'].create({
                            'name': 'property_account_receivable_id',
                            'company_id': company.id,
                            'value_reference': 'account.account,%s' % property_account_receivable.id,
                            'res_id': 'credit.loan.interest,%s' % interest.id,
                            'fields_id': property_account_receivable_id.id,
                            'type': 'many2one'
                        })

                    if main_property_account_payable_id:
                        main_property_account_payable_id.sudo().write({
                            'name': 'property_account_payable_id',
                            'company_id': company.id,
                            'value_reference': 'account.account,%s' % property_account_payable.id,
                            'res_id': 'credit.loan.interest,%s' % interest.id,
                            'fields_id': property_account_payable_id.id,
                            'type': 'many2one'
                        })
                    else:
                        self.env['ir.property'].create({
                            'name': 'property_account_payable_id',
                            'company_id': company.id,
                            'value_reference': 'account.account,%s' % property_account_payable.id,
                            'res_id': 'credit.loan.interest,%s' % interest.id,
                            'fields_id': property_account_payable_id.id,
                            'type': 'many2one'
                        })

                    if main_property_account_income_id:
                        main_property_account_income_id.sudo().write({
                            'name': 'property_account_income_id',
                            'company_id': company.id,
                            'value_reference': 'account.account,%s' % property_account_income.id,
                            'res_id': 'credit.loan.interest,%s' % interest.id,
                            'fields_id': property_account_income_id.id,
                            'type': 'many2one'
                        })
                    else:
                        self.env['ir.property'].create({
                            'name': 'property_account_income_id',
                            'company_id': company.id,
                            'value_reference': 'account.account,%s' % property_account_income.id,
                            'res_id': 'credit.loan.interest,%s' % interest.id,
                            'fields_id': property_account_income_id.id,
                            'type': 'many2one'
                        })

                    if main_property_account_expense_id:
                        main_property_account_expense_id.sudo().write({
                            'name': 'property_account_expense_id',
                            'company_id': company.id,
                            'value_reference': 'account.account,%s' % property_account_expense.id,
                            'res_id': 'credit.loan.interest,%s' % interest.id,
                            'fields_id': property_account_expense_id.id,
                            'type': 'many2one'
                        })
                    else:
                        self.env['ir.property'].create({
                            'name': 'property_account_expense_id',
                            'company_id': company.id,
                            'value_reference': 'account.account,%s' % property_account_expense.id,
                            'res_id': 'credit.loan.interest,%s' % interest.id,
                            'fields_id': property_account_expense_id.id,
                            'type': 'many2one'
                        })

            except Exception as e:
                raise ValidationError(_(str(e)))
            print(values['index'], values['name'], values['company_id'])
            return super(Branch, self).create(values)
        except Exception as e:
            raise UserError(_(str(e)))

class LoanProduct(models.Model):
    _inherit = 'product.template'

    surcharge_id = fields.Many2one('credit.loan.surcharge')
    penalty_id = fields.Many2one('credit.loan.penalty')
    collateral_id = fields.Many2one('credit.loan.collateral', 'Collateral')
    interest_id = fields.Many2one('credit.loan.interest', 'Interest Rate')
    fund_id = fields.Many2one('credit.loan.fund')

class AccountJournal(models.Model):
    _inherit = "account.journal"

    @api.multi
    def allow_update(self):
        for journal in self:
            print(journal)
            journal.write({'update_posted':1})

class CheckingAccountTemplate(models.Model):
    _name = 'credit.check.account.template'

    name = fields.Char()

class CheckingAccount(models.Model):
    _name = 'credit.check.account'

    partnerbank_id = fields.Many2one('res.partner.bank', 'Bank Account')
    bank_id = fields.Many2one('res.bank', 'Bank', related='partnerbank_id.bank_id')
    name = fields.Char(string='Bank Name', related='bank_id.name')
    code = fields.Char(string='Checking Account', related='bank_id.bic')
    status = fields.Selection([('active', 'Active'), ('inactive', 'Inactive')], default='active')
    account_id = fields.Many2one('account.account', 'Asset Account', required=True)
    account = fields.Char(related='account_id.code', string='Account Code')
    account_title = fields.Char(related='account_id.name', string='Account Title')
    template_id = fields.Many2one('credit.check.account.template', 'Check Template')

class ProductSurcharge(models.Model):
    _name = 'credit.loan.surcharge'

    name = fields.Char()
    code = fields.Char()
    description = fields.Text('Description')
    product_ids = fields.One2many('product.template','surcharge_id', 'Applied Products')
    date_created = fields.Datetime('Date Created', default=fields.Datetime.now())
    is_active = fields.Boolean(default=False)
    currency_id = fields.Many2one('res.currency', related='product_ids.currency_id')
    rate = fields.Float('Rate', help='Leave blank if using fixed amount.')
    amount = fields.Monetary('Amount', help='Leave blank if using rate.')
    surcharge_account_payable_id = fields.Many2one('account.account', company_dependent=True,
                                                 string="Payable Account",
                                                 domain=[('deprecated', '=', False)],
                                                 help="This account will be used when validating a customer invoice.")

class ProductPenalty(models.Model):
    _name = 'credit.loan.penalty'

    name = fields.Char()
    code = fields.Char()
    description = fields.Text('Description')
    product_ids = fields.One2many('product.template','penalty_id', 'Applied Products')
    date_created = fields.Datetime('Date Created', default=fields.Datetime.now())
    is_active = fields.Boolean(default=False)
    currency_id = fields.Many2one('res.currency', related='product_ids.currency_id')
    rate = fields.Float('Rate', help='Leave blank if using fixed amount.')
    amount = fields.Monetary(string='Amount', help='Leave blank if using rate.')
    penalty_account_income_id = fields.Many2one('account.account', company_dependent=True,
                                                 string="Income Account",
                                                 domain=[('deprecated', '=', False)],
                                                 help="This account will be used when validating a customer invoice.")

class LoanCollateral(models.Model):
    _name = 'credit.loan.collateral'

    name = fields.Char()
    code = fields.Char()
    description = fields.Text('Description')
    product_ids = fields.One2many('product.template', 'collateral_id','Applied Products')
    collateral_line_ids = fields.One2many('credit.loan.collateral.line','collateral_id','Collaterals')
    date_created = fields.Datetime('Date Created', default=fields.Datetime.now(), readonly=True)
    is_active = fields.Boolean(default=False)
    currency_id = fields.Many2one('res.currency', related='product_ids.currency_id')
    rate = fields.Float('Rate', help='Leave blank if using fixed amount.')
    amount = fields.Monetary(string='Amount', help='Leave blank if using rate.')

class LoanCollateralLines(models.Model):
    _name = 'credit.loan.collateral.line'

    name = fields.Char()
    code = fields.Char()
    collateral_id = fields.Many2one('credit.loan.collateral','Collateral Type')
    status = fields.Selection([('draft','Draft'),('confirm','Confirmed'),('paid','Paid'),('cancel','Cancelled')], default='draft')
    date_created = fields.Datetime('Date created', default=fields.Datetime.now(), readonly=True)
    application_id = fields.Many2one('crm.lead','Applicant')
    currency_id = fields.Many2one('res.currency', related='collateral_id.currency_id')
    rate = fields.Float('Rate', help='Leave blank if using fixed amount.', default=lambda self:self.collateral_id.rate)
    amount = fields.Monetary(string='Amount', help='Leave blank if using rate.', default=lambda self:self.collateral_id.amount)

class LoanInterest(models.Model):
    _name = 'credit.loan.interest'

    name = fields.Char(readonly=True)
    code = fields.Char()
    index = fields.Integer()
    description = fields.Text()
    company_id = fields.Many2one('res.company')
    date_created = fields.Datetime(default=fields.Datetime.now(), string='Date Created', readonly=True)
    rate = fields.Float('Rate', help='Leave blank if using fixed amount.')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    amount = fields.Monetary(string='Amount', help='Leave blank if using rate.')
    product_ids = fields.One2many('product.template', 'interest_id', 'Applied Products')
    is_active = fields.Boolean(default=True)
    property_account_receivable_id = fields.Many2one('account.account',
        string="Receivable Account",
        domain=[('deprecated', '=', False),('internal_type','=','receivable')],
        help="This account will be used when validating a customer invoice.")
    property_account_payable_id = fields.Many2one('account.account', company_dependent=True,
                                                 string="Payable Account",
                                                 domain=[('deprecated', '=', False),('internal_type','=','payable')],
                                                 help="This account will be used when validating a customer invoice.")
    property_account_income_id = fields.Many2one('account.account', company_dependent=True,
                                                 string="Income Account",
                                                 domain=[('deprecated', '=', False),('internal_type','=','other')],
                                                 help="This account will be used when validating a customer invoice.")
    property_account_expense_id = fields.Many2one('account.account', company_dependent=True,
                                                 string="Expense Account",
                                                 domain=[('deprecated', '=', False),('internal_type','=','other')],
                                                 help="This account will be used when validating a customer invoice.")
    # interest_account_expense_id = fields.Many2one('account.account', company_dependent=True,
    #     string="Payable Account",
    #     domain=[('deprecated', '=', False)],
    #     help="The expense is accounted for when a vendor bill is validated, except in anglo-saxon accounting with perpetual inventory valuation in which case the expense (Cost of Goods Sold account) is recognized at the customer invoice validation.")

    @api.model
    def create(self, values):
        values['code'] = 'INT'
        values['index'] = int(self.search([], order='index desc', limit=1).index) + 1
        values['name'] = '%s-%s' %(values['code'],values['index'])

        return super(LoanInterest, self).create(values)

class LoanFund(models.Model):
    _name = 'credit.loan.fund'

    name = fields.Char()
    code = fields.Char()
    description = fields.Text('Description')
    product_ids = fields.One2many('product.template','fund_id', 'Applied Products')
    date_created = fields.Datetime('Date Created', default=fields.Datetime.now())
    is_active = fields.Boolean(default=False)
    currency_id = fields.Many2one('res.currency', related='product_ids.currency_id')
    rate = fields.Float('Rate', help='Leave blank if using fixed amount.')
    amount = fields.Monetary(string='Amount', help='Leave blank if using rate.')

