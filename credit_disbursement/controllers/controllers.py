# -*- coding: utf-8 -*-
from odoo import http

# class CreditDisbursement(http.Controller):
#     @http.route('/credit_disbursement/credit_disbursement/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/credit_disbursement/credit_disbursement/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('credit_disbursement.listing', {
#             'root': '/credit_disbursement/credit_disbursement',
#             'objects': http.request.env['credit_disbursement.credit_disbursement'].search([]),
#         })

#     @http.route('/credit_disbursement/credit_disbursement/objects/<model("credit_disbursement.credit_disbursement"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('credit_disbursement.object', {
#             'object': obj
#         })