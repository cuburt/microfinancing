# -*- coding: utf-8 -*-
from odoo import http

# class CreditCrm(http.Controller):
#     @http.route('/credit_crm/credit_crm/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/credit_crm/credit_crm/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('credit_crm.listing', {
#             'root': '/credit_crm/credit_crm',
#             'objects': http.request.env['credit_crm.credit_crm'].search([]),
#         })

#     @http.route('/credit_crm/credit_crm/objects/<model("credit_crm.credit_crm"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('credit_crm.object', {
#             'object': obj
#         })