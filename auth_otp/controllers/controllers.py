# -*- coding: utf-8 -*-
from odoo import http

# class AuthOtp(http.Controller):
#     @http.route('/auth_otp/auth_otp/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/auth_otp/auth_otp/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('auth_otp.listing', {
#             'root': '/auth_otp/auth_otp',
#             'objects': http.request.env['auth_otp.auth_otp'].search([]),
#         })

#     @http.route('/auth_otp/auth_otp/objects/<model("auth_otp.auth_otp"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('auth_otp.object', {
#             'object': obj
#         })