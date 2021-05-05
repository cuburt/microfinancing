# -*- coding: utf-8 -*-
from odoo import http
import os
from twilio.rest import Client

class Twilio(http.Controller):
    @http.route('/twilio/send_sms/', auth='public')
    def index(self, **kw):
        account_sid = 'ACeca753006d9cf9dae993a9ade93bd98a'
        auth_token = '7d69d0146f510cdd93ffdf100898a1d0'
        client = Client(account_sid, auth_token)

        client.messages.create(
            messaging_service_sid="MG682f266dadbab733791dc5956baea263",
            body="Hello, world",
            to="+639197867033"
        )

