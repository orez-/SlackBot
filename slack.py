import json
import threading

import requests
import websocket

import config


class SlackError(Exception):
    pass


class SlackAPI(object):
    API_URL = 'https://slack.com/api/'

    def __init__(self, bot):
        self._bot = bot
        self._listeners = []

    def start_listening(self, listener):
        self._listeners.append(listener)

    def connect(self):
        self._request_data = self.send_web('rtm.start', {})
        if not self._request_data['ok']:
            raise SlackError(self._request_data['error'])

        _ims = self._request_data[u'ims']
        self._bot.users = {v[u'id']: v for v in self._request_data.pop(u'users')}
        for user_id, user in self._bot.users.iteritems():
            user[u'im'] = next((im[u'id'] for im in _ims if im[u'user'] == user_id), None)
        self._bot._channels = self._request_data.pop(u'channels')
        _self = self._request_data.pop(u'self')
        self._bot.user_name = _self[u'name']
        self._bot.user = _self[u'id']

        self._connect_websocket(self._request_data['url'])

    def _connect_websocket(self, url):
        self._ws = websocket.WebSocketApp(
            url,
            on_message=self._on_receive,
            on_error=self._on_ws_error,
        )

        t = threading.Thread(target=self._ws.run_forever)
        t.setDaemon(True)
        t.start()

    def _on_ws_error(self, ws, error):
        print error
        print "Reconnecting..."
        self.connect()

    def _on_receive(self, ws, message):
        response = json.loads(message)
        for listener in self._listeners:
            listener(response)

    def send(self, payload):
        self._ws.send(json.dumps(payload))

    def send_web(self, message_type, payload):
        payload = dict(payload)
        payload.update({'token': config.token})
        return requests.post(SlackAPI.API_URL + message_type, data=payload, verify=False).json()
