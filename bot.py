from __future__ import  absolute_import, print_function

import collections
import hashlib
import imp
import os
import Queue
import re
import sys
import threading
import time
import traceback

import config
import exception
import module_thread
import modules
import slack
import util

home = os.getcwd()


class _SlackBotWrapper(object):
    def __init__(self, bot, msg):
        object.__setattr__(self, '_bot', bot)
        object.__setattr__(self, '_msg', msg)
        object.__setattr__(self, 'channel', bot.get_channel(msg.get(u'channel')))

    def reply(self, message):
        self.say(message, self._msg[u'channel'])

    def __getattr__(self, other):
        """Default to _bot's methods"""
        return getattr(self._bot, other)

    def __setattr__(self, other, value):
        raise Exception("Bot may not have properties assigned to it from a module.")


class SlackBot(object):
    def __init__(self):
        self._message_id = int(time.time())
        self._incoming_messages = Queue.Queue()
        self.pending_outgoing_messages = {}
        self.previous_messages = collections.deque()

        self.config = {
            'send_channel': config.default_channel,
            'terminal_ping': config.terminal_ping,
        }

        self._slack_api = slack.SlackAPI(self)
        self._slack_api.connect()
        self._slack_api.start_listening(self._listener)
        self._debug_fn = None

        self.commands = []
        self.load_all_modules()

        t = threading.Thread(target=self._dispatcher)
        t.setDaemon(True)
        t.start()

    def _listener(self, message):
        """
        The listener simply enqueues the message to ensure we're
        able to listen for any further messages immediately.
        """
        self._incoming_messages.put(message)

    def parse_destination(self, destination):
        if destination[0] == "#":
            return self.get_channel_id(destination[1:])
        elif destination[0] == "@":
            return self.get_user_im(destination[1:])
        return destination

    def say(self, text, channel):
        if not text:
            return
        if not isinstance(text, unicode):
            text = unicode(str(text), 'utf8')
        channel = self.parse_destination(channel)
        if len(text) > util.MAX_MESSAGE_LENGTH:
            raise exception.MessageTooLongException
        message = dict(
            id=self._message_id,
            type='message',
            channel=channel,
            text=self._format_outgoing(text),
        )
        self.pending_outgoing_messages[self._message_id] = {u'text': text, u'channel': channel}
        self._message_id += 1
        self._slack_api.send(message)

    def edit_message(self, timestamp, channel, new_text):
        """
        Given the timestamp and channel of a previously sent message,
        replace the text with the specified new_text.
        """
        # TODO: This signature is pretty rough from a usability
        # standpoint. Maybe abstract away the millisecond timestamp
        # in favor of message matching? Possibly utilize Slack's PING
        # functionality??
        self._slack_api.send_web('chat.update', dict(
            ts=timestamp,
            channel=channel,
            text=new_text,
        ))

    def open_dm(self, user):
        """
        Request a direct message channel a user by @username or user id.
        """
        user = self._parse_user_id(user)
        return self._slack_api.send_web('im.open', dict(user=user))

    def close_dm(self, user):
        """
        Request a direct message channel between a user and this bot be
        closed. NB: Slack seems to ignore this outright.
        """
        user = self._parse_user_id(user)
        dm = self.users[user][u'im']
        if dm:
            return self._slack_api.send_web('im.close', dict(channel=dm))

    def _format_outgoing(self, msg):
        msg = re.sub(r"(^| )@(\w+)\b", self._format_user_mention, msg)
        msg = re.sub(r"(^| )#(\w+)\b", self._format_channel_mention, msg)
        return msg

    def _format_user_mention(self, match):
        start, nick = match.groups()
        user_id = self.get_user_id(nick)
        if user_id:
            return "{}<@{}>".format(start, user_id)
        elif nick in ('channel', 'everyone', 'group'):
            return "{}<!{}>".format(start, nick)
        return match.group(0)

    def _format_channel_mention(self, match):
        start, channel = match.groups()
        channel_id = self.get_channel_id(channel)
        if channel_id:
            return "{}<#{}>".format(start, channel_id)
        return match.group(0)

    def _format_incoming(self, incoming):
        try:
            incoming[u'channel_name'] = self.get_channel_name(incoming[u'channel'])
        except:
            pass
        if u'user' in incoming:
            username = self.get_nick(incoming[u'user'])
            if username:
                incoming[u'user_name'] = username
        if u'<http' in incoming.get(u'text', ''):
            text = incoming[u'text']
            incoming[u'text'] = re.sub(r'<(http[^>]+)>', r'\1', text)

    def _dispatcher(self):
        """
        Receive messages and route them to functionality.
        """
        while 1:
            try:
                response = self._incoming_messages.get(block=True)
                self._format_incoming(response)
                now = time.time()
                # match the event to the best command
                for command in self.commands[:]:
                    if command.deadline is not False and command.deadline < now:
                        self.unregister_command(command)  # silently remove him
                        continue
                    match = command.matches(self, response)
                    if match:
                        command(_SlackBotWrapper(self, response), response, *match.groups())
                        if command.activations is not False and command.activations <= 0:
                            self.unregister_command(command)
            except Exception:
                self.debug(u'\n'.join([traceback.format_exc(), str(response)]), 'red')
            else:
                try:
                    if u'_logged' not in response:
                        self.debug(response, 'gray')
                except:
                    print("Wow something went REAL wrong.")

    def set_debug_fn(self, fn):
        self._debug_fn = fn

    def debug(self, string, color=None):
        if self._debug_fn:
            return self._debug_fn(string, color)
        else:
            print(string)

    def die(self):
        sys.exit(0)

    # ===
    def get_nick(self, user_id):
        try:
            return self.users[user_id][u'name']
        except TypeError:
            return None

    def get_user_id(self, name):
        return next((u[u'id'] for u in self.users.itervalues() if u[u'name'] == name), None)

    def get_user_im(self, name):
        return next((u[u'im'] for u in self.users.itervalues() if u[u'name'] == name), None)

    def _get_channel(self, conditional, prop=None):
        return next((c[prop] if prop else c for c in self._channels if conditional(c)), None)

    def get_channel(self, channel_id):
        return self._get_channel(lambda c: c[u'id'] == channel_id)

    def get_channel_id(self, name):
        return self._get_channel(lambda c: c[u'name'] == name, u'id')

    def get_channel_name(self, channel_id):
        channel_name = None
        if channel_id.startswith('C'):
            formatter = "#{}".format
            channel_name = self._get_channel(lambda c: c[u'id'] == channel_id, u'name')
        elif channel_id.startswith('D'):
            formatter = "@{}".format
            channel_name = next((
                user[u'name']
                for user in self.users.itervalues()
                if user[u'im'] == channel_id), None)
        if channel_name:
            channel_name = formatter(channel_name)
        return channel_name

    def get_channel_members(self, channel_id):
        return self._get_channel(lambda c: c[u'id'] == channel_id, u'members')

    def get_channel_names(self):
        return [channel[u'name'] for channel in self._channels]

    def _parse_user_id(self, user):
        at_hint = " Perhaps you omitted the '@'?"
        if user.startswith("@"):
            at_hint = ""
            user_id = self.get_user_id(user[1:])
            if user_id:
                return user_id
        elif user.startswith("U"):
            if user in self.users:
                return user
        raise Exception("Could not parse '{}' as user.{}".format(user, at_hint))

    # Module methods
    def get_module_path(self, name):
        """Get the path to the module of the given name."""
        return os.path.join(home, 'modules', '{}.py'.format(name))

    def find_module_paths(self):
        """Find all the files in /modules/"""
        filenames = []
        for mod in os.listdir(os.path.join(home, 'modules')):
            if mod.endswith('.py') and not mod.startswith('_'):
                filenames.append(os.path.join(home, 'modules', mod))
        return filenames

    def load_all_modules(self):
        """Load all the modules from the /modules/ directory"""
        for filename in self.find_module_paths():
            name = os.path.basename(filename)[:-3]
            self.load_module(name, filename)

    def load_module(self, name, filename=None):
        """
        Load a module, overwriting the previous module if possible
        Return an Exception, or None if no exception.
        """
        if filename is None:
            filename = self.get_module_path(name)
        cmds = self.commands[:]  # backup the commands (in case of failure)
        module_cmds = None
        module_id = self.get_module_id(name)
        if module_id in modules.register.modules:
            # unload the old module to make room for the new one, but remember it
            # in case something goes wrong when loading the new module.
            module_cmds = self.unload_module(module_id)
        try:
            # commands are registered automatically
            module = imp.load_source(module_id, filename)
            # # If you decide to use a setup method uncomment this,
            # # although actually it would probably be better as an
            # # explicit decorator. Ones for 'onload', 'onunload',
            # # stuff like that.
            # if hasattr(module, "setup"):
            #     module.setup()
        except Exception as e:
            self.debug(
                "{}\nError loading {}: {} (in bot.py)".format(traceback.format_exc(), module_id, e),
                'red'
            )
            self.commands = cmds  # replace commands' previous state
            if module_cmds is not None:
                modules.register.load_module(module_id, module_cmds)  # reload module's previous state
            elif module_id in modules.register.modules:  # loaded a couple commands
                modules.register.unload_module(module_id)
            return e
        else:
            commands = modules.register.module(module_id)
            if commands is not None:
                self.register_commands(commands)
        return None

    def register_commands(self, commands):
        self.commands.extend(commands)
        self.commands.sort(key=lambda cmd: -cmd.priority)

    def unregister_command(self, command):
        # TODO: Since commands are priority-ordered you could binary search
        self.commands.remove(command)
        modules.register.unregister_command(command)

    def unload_module(self, module_id):
        unregistered_commands = modules.register.unload_module(module_id)
        for command in unregistered_commands:
            # TODO: Also binary search here?
            self.commands.remove(command)
        return unregistered_commands

    @staticmethod
    def get_module_id(name):
        return "{}_{}".format(name, hashlib.md5(name).hexdigest())


if __name__ == "__main__":
    bot = SlackBot()

    try:
        while 1:
            pass
    except (EOFError, KeyboardInterrupt):
        bot.debug("Press Enter to continue shutdown.")
        module_thread.join_threads()
    print("\nBe seeing you ...")
    bot.die()
