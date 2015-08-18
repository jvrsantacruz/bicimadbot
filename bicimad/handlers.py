# -*- coding: utf-8 -*-
import os
import logging

from bottle import request, Bottle, abort

from . import bicimad
from . import telegram


app = Bottle()
app.config.load_config(os.getenv(u'APP_CONFIG'))
log = logging.getLogger('bicimad.app')


@app.post('/webhook/<token>')
def webhook(token):
    if token != app.config.get('telegram.token'):
        log.info(u'Unknown token: %s', token)
        abort(401, u'Not my token')

    tgram_api = telegram.Telegram.from_config(app.config)
    bmad_api = bicimad.BiciMad.from_config(app.config)
    telegram.process_updates(request.json, app.config, tgram_api, bmad_api)
