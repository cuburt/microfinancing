# -*- coding: utf-8 -*-
from odoo import http

# class CreditInvestigation(http.Controller):
#     @http.route('/credit_investigation/credit_investigation/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/credit_investigation/credit_investigation/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('credit_investigation.listing', {
#             'root': '/credit_investigation/credit_investigation',
#             'objects': http.request.env['credit_investigation.credit_investigation'].search([]),
#         })

#     @http.route('/credit_investigation/credit_investigation/objects/<model("credit_investigation.credit_investigation"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('credit_investigation.object', {
#             'object': obj
#         })