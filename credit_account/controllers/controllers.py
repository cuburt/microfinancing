# -*- coding: utf-8 -*-
from odoo import http

# class CreditAccount(http.Controller):
#     @http.route('/credit_account/credit_account/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/credit_account/credit_account/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('credit_account.listing', {
#             'root': '/credit_account/credit_account',
#             'objects': http.request.env['credit_account.credit_account'].search([]),
#         })

#     @http.route('/credit_account/credit_account/objects/<model("credit_account.credit_account"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('credit_account.object', {
#             'object': obj
#         })