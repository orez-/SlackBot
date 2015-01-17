import Queue
import re
import threading
import traceback

import slack


class SlackBot(object):
    def __init__(self):
        self._incoming_messages = Queue.Queue()

        self._slack_api = slack.SlackAPI()
        self._slack_api.connect()
        self._slack_api.start_listening(self._listener)
        t = threading.Thread(target=self._dispatcher)
        t.setDaemon(True)
        t.start()

    def _listener(self, message):
        """
        The listener simply enqueues the message to ensure we're
        able to listen for any further messages immediately.
        """
        self._incoming_messages.put(message)

    def _dispatcher(self):
        while 1:
            try:
                response = self._incoming_messages.get(block=True)
                if u'channel' in response:
                    response[u'channel_name'] = self._slack_api.get_channel_name(response[u'channel'])
                if u'user' in response:
                    username = self._slack_api.get_nick(response[u'user'])
                    if username:
                        response[u'user_name'] = username

                if response.get('type') == "message" and 'text' in response:
                    text = re.sub(
                        r"<@([^>]+)>",
                        lambda match: self._slack_api.get_nick(match.group(1)),
                        response['text'],
                    )
                    message = "{}: {}".format(
                        response['user_name'],
                        text,
                    )
                    if "frankling" in text:
                        self.send(
                            "Hi @{user}!".format(user=response['user_name']),
                            response['channel_name'],
                        )
                    print message
                else:
                    print response
            except Exception as e:
                traceback.print_exc()
                print response

    def send(self, text, channel):
        if not text:
            return
        channel = self._slack_api.get_channel_id(channel)
        message = dict(
            type="message",
            channel=channel,
            text=text,
        )
        self._slack_api.send(message)


frankling = SlackBot()


while 1:
    message = raw_input()
    frankling.send(message, channel="bot_test")
