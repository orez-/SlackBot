from __future__ import print_function

import functools
import traceback

import modules
import util


# CLI Display methods.
def _log_message(bot, channel, user, text):
    with util.hilite('cyan'):
        print(channel, end=' ')
    with util.hilite('purple'):
        print(user, end=' ')
    print(_format_text(bot, text))


def _format_user(bot, match):
    user_id, = match.groups()
    user = bot.get_nick(user_id)
    if user:
        if user_id == bot.user:
            user = "{}\a".format(user)
        return util.hilite_string('cyan', "@{}".format(user))
    return match.group(0)


def _format_channel(bot, match):
    channel_id, = match.groups()
    channel = bot.get_channel_name(channel_id)
    if channel:
        return util.hilite_string('cyan', "#{}".format(channel))
    return match.group(0)


def _format_notice(bot, match):
    notice, = match.groups()
    if notice in ('channel', 'everyone', 'group'):
        return util.hilite_string('cyan', "@{}\a".format(notice))
    return match.group(0)


def _format_link(bot, match):
    url, = match.groups()
    return util.hilite_string('blue', url)


_format_text = functools.partial(
    util.format_incoming_text,
    user_fn=_format_user,
    channel_fn=_format_channel,
    notice_fn=_format_notice,
    url_fn=_format_link,
)


# CLI outgoing
def _channel(bot, command):
    if len(command) == 1:
        print("Currently sending to", end=' ')
    else:
        bot.config['send_channel'] = command[1]
        print("Set channel to", end=' ')
    with util.hilite('cyan'):
        print(bot.config['send_channel'], end='')
    print(".")


def _show_typing(bot, command):
    if len(command) < 2:
        return
    setting = command[1]
    bot.config['show_typing'] = setting != '0'


def _bot(bot, command):
    print(eval(command[1]))


@modules.register(actions=['hello'], threaded=True, hide=True, occludes=False, priority=10)
def cli_input(bot, msg):
    while 1:
        try:
            message = raw_input()
            if message[:1] == "/":
                command = message.split()
                if command[0] == "/channel":
                    _channel(bot, command)
                elif command[0] == "/show_typing":
                    _show_typing(bot, command)
                elif command[0] == "/bot":
                    _bot(bot, command)
            else:
                bot.say(message, channel=bot.config['send_channel'])
        except:
            with util.hilite('red'):
                print("Error on output:")
                traceback.print_exc()

# ===


@modules.register(rule=r'.*', hide=True, occludes=False, priority=10)
def log_message(bot, msg):
    """
    Print to the terminal a message that someone has written.
    """
    msg[u'_logged'] = True
    _log_message(bot, msg[u'channel_name'], msg[u'user_name'], msg[u'text'])


@modules.register(
    actions=[None], hide=True, occludes=False, fields=dict(reply_to=any), priority=10)
def log_received(bot, msg):
    """
    Print to the terminal a message the bot has said.
    """
    msg[u'_logged'] = True
    _log_message(bot, bot.get_channel_name(msg[u'channel']), bot.user_name, msg[u'text'])


@modules.register(actions=['user_typing'], occludes=False, hide=True, priority=10)
def log_typing(bot, msg):
    """
    Print to the terminal that a user is typing.

    Note that if the bot config `show_typing` is False
    nothing will be logged.
    """
    msg[u'_logged'] = True
    if bot.config.get('show_typing'):
        with util.hilite('gray'):
            if msg[u'channel_name']:
                print('{} is typing in {}.'.format(msg[u'user_name'], msg[u'channel_name']))
            else:
                print('{} is typing to you.'.format(msg[u'user_name']))


@modules.register(actions=['presence_change'], occludes=False, hide=True, priority=10)
def log_presence_change(bot, msg):
    """
    Print to the terminal that a user has changed presence.
    """
    msg[u'_logged'] = True
    with util.hilite('gray'):
        print('{} is now '.format(msg[u'user_name']), end='')
        color = {
            u'active': 'green',
            u'away': 'yellow',
        }[msg[u'presence']]
        with util.hilite(color):
            print(msg[u'presence'], end='')
        print(".")


@modules.register(fields=dict(subtype='message_changed'), occludes=False, hide=True, priority=10)
def log_message_changed(bot, msg):
    """
    Print to the terminal that a user's message has been edited.

    Note that this does not necessarily mean the user has edited their
    message. Automatic unfurling in particular is handled
    via message_changed.
    """
    msg[u'_logged'] = True
    with util.hilite('gray'):
        print("edited", end=" ")
    message = msg[u'message']
    _log_message(
        bot,
        msg[u'channel_name'],
        bot.get_nick(message[u'user']),
        message[u'text'],
    )
