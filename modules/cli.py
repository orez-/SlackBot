from __future__ import print_function

import contextlib
import functools
import readline
import sys
import threading
import traceback

import modules
import util


@contextlib.contextmanager
def autoflush(bot):
    sys.stdout.write("\r\033[K")  # Clear line.
    try:
        yield
    finally:
        line_buffer = readline.get_line_buffer()
        print(get_cli_prefix(bot), end="")  # Prefix string
        print(line_buffer, end="")
        sys.stdout.flush()


def get_cli_prefix(bot):
    return "[{}] ".format(util.hilite_string('cyan', bot.config['send_channel']))


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
        if user_id == bot.user and bot.config['terminal_ping']:
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
        return util.hilite_string('cyan', "@{}{}".format(
            notice,
            "\a" if bot.config['terminal_ping'] else ""))
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


def _config_boolean(config_id, name, default):
    def anon(bot, command):
        if len(command) >= 2:
            setting = command[1]
            bot.config[config_id] = setting != '0'
        with util.hilite('gray'):
            print(name, end=": ")
        config_item = bot.config.get(config_id, default)
        with util.hilite('green' if config_item else 'red'):
            print(config_item)
    anon.__name__ = '_{}'.format(config_id)
    return anon


def _bot(bot, command):
    print(eval(' '.join(command[1:])))


def _unknown_command(bot, command):
    with util.hilite('gray'):
        print("Unknown command '{}'".format(command[0]))


def _setup_autocompletion(bot):
    def completer(text, state):
        if text.startswith('@'):
            users = (user[u'name'] for user in bot.users.itervalues())
            matched = [user for user in users if user.startswith(text[1:])]
        elif text.startswith('#'):
            matched = [channel for channel in bot.get_channel_names() if channel.startswith(text[1:])]
        else:
            return None
        try:
            return text[0] + matched[state] + " "
        except KeyError:
            return None

    def show_matches(substitution, matches, longest_match_length):
        with autoflush(bot):
            print(' '.join(matches))

    readline.set_completer_delims(' \t\n;')
    readline.set_completer(completer)
    if 'libedit' in readline.__doc__:
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")
    readline.set_completion_display_matches_hook(show_matches)


def _get_debug_fn(bot):
    def debug_fn(string, color):
        with autoflush(bot):
            if color is not None:
                string = util.hilite_string(color, string)
            print(string)
    return debug_fn


@modules.register(actions=['hello'], threaded=True, hide=True, occludes=False, priority=100)
def cli_input(bot, msg):
    bot.set_debug_fn(_get_debug_fn(bot))
    current_thread = threading.current_thread()
    _setup_autocompletion(bot)
    command_list = {
        'bot': _bot,
        'channel': _channel,
        'show_typing': _config_boolean('show_typing', "Show typing", False),
        'terminal_ping': _config_boolean('terminal_ping', "Terminal ping", True),
    }
    while 1:
        try:
            message = raw_input(get_cli_prefix(bot))
            print("\033[A\033[K", end='\r')  # Clear the raw_input line.
            if current_thread.stopped():
                return
            if message[:1] == "/":
                command = message.split()
                command_list.get(command[0][1:], _unknown_command)(bot, command)
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
    with autoflush(bot):
        _log_message(bot, msg[u'channel_name'], msg[u'user_name'], msg[u'text'])


@modules.register(
    actions=[None], hide=True, occludes=False, fields=dict(reply_to=any), priority=10)
def log_received(bot, msg):
    """
    Print to the terminal a message the bot has said.
    """
    msg[u'_logged'] = True
    with autoflush(bot):
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
        with autoflush(bot), util.hilite('gray'):
            if msg[u'channel_name'].startswith('#'):
                print('{} is typing in {}.'.format(msg[u'user_name'], msg[u'channel_name']))
            else:
                print('{} is typing to you.'.format(msg[u'user_name']))


@modules.register(actions=['presence_change'], occludes=False, hide=True, priority=10)
def log_presence_change(bot, msg):
    """
    Print to the terminal that a user has changed presence.
    """
    msg[u'_logged'] = True
    with autoflush(bot), util.hilite('gray'):
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
    with autoflush(bot):
        with util.hilite('gray'):
            print("edited", end=" ")
        message = msg[u'message']
        _log_message(
            bot,
            msg[u'channel_name'],
            bot.get_nick(message[u'user']),
            message[u'text'],
        )


@modules.register(actions=['star_added'], occludes=False, hide=True, priority=10)
def log_starred(bot, msg):
    item = msg[u'item']
    if item[u'type'] in ['message', 'channel', 'file', 'im']:
        with autoflush(bot):
            msg[u'_logged'] = True
            with util.hilite('yellow'):
                print(msg[u'user_name'], end=" starred ")
            _print_star_info(bot, msg)


@modules.register(actions=['star_removed'], occludes=False, hide=True, priority=10)
def log_unstarred(bot, msg):
    item = msg[u'item']
    if item[u'type'] in ['message', 'channel', 'file', 'im']:
        with autoflush(bot):
            msg[u'_logged'] = True
            print(msg[u'user_name'], end=" unstarred ")
            _print_star_info(bot, msg)


def _print_star_info(bot, msg):
    item = msg[u'item']
    if item[u'type'] == 'message':
        message = item[u'message']
        _log_message(
            bot,
            bot.get_channel_name(item[u'channel']),
            bot.get_nick(message[u'user']),
            message[u'text'],
        )
    elif item[u'type'] in ('channel', 'im'):
        channel = item[u'channel']
        with util.hilite('purple'):
            print(bot.get_channel_name(channel))
    elif item[u'type'] == 'file':
        sent_file = item[u'file']
        message = sent_file[u'permalink_public']
        with util.hilite('purple'):
            print(bot.get_nick(sent_file[u'user']), end=" ")
        with util.hilite('blue'):
            print(message)


@modules.register(actions=['team_join'], hide=True, occludes=False, priority=10)
def log_new_user(bot, msg):
    msg[u'_logged'] = True
    user = msg[u'user']
    with autoflush(bot):
        with util.hilite('cyan'):
            print(user[u'name'], end=" ")
        print("({}) has joined the team!".format(user[u'real_name']))


@modules.register(actions=['file_public', 'file_shared'], hide=True, occludes=False, priority=10)
def log_image(bot, msg):
    permalink = msg[u'file'].get(u'permalink_public')
    if permalink:
        msg[u'_logged'] = True
        with autoflush(bot), util.hilite('blue'):
            print(permalink)
