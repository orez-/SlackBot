from __future__ import print_function

import modules
import util


# CLI Display methods.
def _log_message(channel, user, text):
    with util.hilite('cyan'):
        print(channel, end=' ')
    with util.hilite('purple'):
        print(user, end=' ')
    print(text)


@modules.register()
def log_message(bot, msg):
    msg[u'_logged'] = True
    _log_message(msg[u'channel_name'], msg[u'user_name'], msg[u'text'])


@modules.register(actions=[None], fields=dict(reply_to=any))
def log_received(bot, msg):
    msg[u'_logged'] = True
    _log_message(bot.get_channel_name(msg[u'channel']), bot.user_name, msg[u'text'])


@modules.register(actions=['user_typing'])
def log_typing(bot, msg):
    msg[u'_logged'] = True
    with util.hilite('gray'):
        if msg[u'channel_name']:
            print('{} is typing in {}.'.format(msg[u'user_name'], msg[u'channel_name']))
        else:
            print('{} is typing to you.'.format(msg[u'user_name']))


@modules.register(actions=['presence_change'])
def log_presence_change(bot, msg):
    msg[u'_logged'] = True
    with util.hilite('gray'):
        print('{} is now '.format(msg[u'user_name']), end='')
        color = {
            u'active': 'green',
            u'away': 'yellow',
            u'offline': 'red',
        }[msg[u'presence']]
        with util.hilite(color):
            print(msg[u'presence'], end='')
        print(".")
