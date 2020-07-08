# -*- coding: utf-8 -*-
from odoo import http

# class CreditApplication(http.Controller):
#     @http.route('/credit_application/credit_application/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/credit_application/credit_application/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('credit_application.listing', {
#             'root': '/credit_application/credit_application',
#             'objects': http.request.env['credit_application.credit_application'].search([]),
#         })

#     @http.route('/credit_application/credit_application/objects/<model("credit_application.credit_application"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('credit_application.object', {
#             'object': obj
#         })