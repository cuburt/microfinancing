# -*- coding: utf-8 -*-
from odoo import http

# class CreditProcessing(http.Controller):
#     @http.route('/credit_processing/credit_processing/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/credit_processing/credit_processing/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('credit_processing.listing', {
#             'root': '/credit_processing/credit_processing',
#             'objects': http.request.env['credit_processing.credit_processing'].search([]),
#         })

#     @http.route('/credit_processing/credit_processing/objects/<model("credit_processing.credit_processing"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('credit_processing.object', {
#             'object': obj
#         })