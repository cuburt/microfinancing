# -*- coding: utf-8 -*-
from odoo import http

# class CreditSme(http.Controller):
#     @http.route('/credit_sme/credit_sme/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/credit_sme/credit_sme/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('credit_sme.listing', {
#             'root': '/credit_sme/credit_sme',
#             'objects': http.request.env['credit_sme.credit_sme'].search([]),
#         })

#     @http.route('/credit_sme/credit_sme/objects/<model("credit_sme.credit_sme"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('credit_sme.object', {
#             'object': obj
#         })