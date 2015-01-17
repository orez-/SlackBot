import json
import threading

import requests
import websocket

import config


class SlackError(Exception):
    pass


class SlackAPI(object):
    API_URL = 'https://slack.com/api/'

    def start_listening(self, listener):
        t = threading.Thread(target=self._receiver, args=(listener, ))
        t.setDaemon(True)
        t.start()

    def connect(self):
        url = "{}rtm.start".format(SlackAPI.API_URL)
        params = {'token': config.token}
        self._request_data = requests.post(url, data=params, verify=False).json()
        if not self._request_data['ok']:
            raise SlackError(self._request_data['error'])

        self.users = {v[u'id']: v for v in self._request_data.pop(u'users')}
        self._channels = self._request_data.pop(u'channels')
        self._ws_connection = websocket.create_connection(self._request_data['url'])

    def get_nick(self, user_id):
        try:
            return self.users[user_id][u'name']
        except TypeError:
            return None

    def get_channel_id(self, name):
        channel = next((c for c in self._channels if c[u'name'] == name), None)
        if channel:
            return channel[u'id']
        return None

    def get_channel_name(self, channel_id):
        channel = next((c for c in self._channels if c[u'id'] == channel_id), None)
        if channel:
            return channel[u'name']
        return None

    def _receiver(self, listener):
        while 1:
            response = json.loads(self._ws_connection.recv())
            listener(response)

    def send(self, payload):
        self._ws_connection.send(json.dumps(payload))
