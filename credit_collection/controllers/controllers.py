# -*- coding: utf-8 -*-
from odoo import http

# class CreditCollection(http.Controller):
#     @http.route('/credit_collection/credit_collection/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/credit_collection/credit_collection/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('credit_collection.listing', {
#             'root': '/credit_collection/credit_collection',
#             'objects': http.request.env['credit_collection.credit_collection'].search([]),
#         })

#     @http.route('/credit_collection/credit_collection/objects/<model("credit_collection.credit_collection"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('credit_collection.object', {
#             'object': obj
#         })