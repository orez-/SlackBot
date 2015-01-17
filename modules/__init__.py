import re
import time

import config


def valid_regex(regex):
    try:
        re.compile(regex)
    except re.error:
        return False
    else:
        return True


class BotCommand(object):
    RULE_VERSION = 0

    def __init__(
            self, fn,
            rule=None, actions=["message"], priority=0, sender=None,
            ttl=False, activations=False):
        self._fn = fn

        self._rule = rule  # unmodified base rule, for reference
        self._compiled_rule = None  # regex object to match against
        self._rule_version = None

        self._sender = sender  # unmodified base sender, for reference
        self._compiled_sender = None  # regex object to match against

        self.actions = list(actions)  # list of irc actions to activate on

        self.priority = priority
        if ttl:
            self.deadline = time.time() + int(ttl)
        else:
            self.deadline = False
        if activations:
            self.activations = int(activations)
        else:
            self.activations = False

    @property
    def sender(self):
        """
        Get the regex that matches sender on which to trigger.
        If the regex does not exist, generates it.
        """
        if self._compiled_sender is None:
            if isinstance(self._sender, str):
                sender = self._sender
            elif isinstance(self._sender, list):
                if not all(map(valid_regex, self._sender)):
                    raise ValueError("all elements in sender list must be valid regex")
                sender = "^%s$" % r'|'.join("(?:%s)" % nick for nick in self._sender)
            elif self._sender is None:
                sender = r'.*'
            else:
                raise ValueError("invalid sender format")
            self._compiled_sender = re.compile(sender)
        return self._compiled_sender

    @property
    def rule(self):
        """
        Get the regex that matches input on which to trigger.
        If the regex does not exist or is out of date, generates it.
        """
        if self._compiled_rule is None or self._rule_version != BotCommand.RULE_VERSION:
            if self._rule is None:
                rule = r".*"
            elif isinstance(self._rule, str):
                rule = self._rule
            elif isinstance(self._rule, list):
                rule = r'\s+'.join(self._rule)
            else:
                raise ValueError("invalid rule format")
            self._rule_version = BotCommand.RULE_VERSION
            self._compiled_rule = re.compile(rule)
        return self._compiled_rule

    def matches(self, msg):
        """Determine if the given message should trigger this command."""
        # If action is PING sender is None, safe to fall through.
        # if not (msg.sender is None or self.sender.match(msg.sender)):
        #     return False
        if msg.get('type') not in self.actions:
            return False
        return self.rule.match(msg['text'])

    def __call__(self, bot, msg, *args):
        """Run the command's function."""
        if self.activations:
            self.activations -= 1
        return self._fn(bot, msg, *args)

    def __repr__(self):
        return self._fn.__name__


class register(object):
    """
    Registers the decorated function as a command of the bot.
    """
    modules = {}

    def __new__(cls, *args, **kwargs):
        def decorator(fn):
            new_func = BotCommand(fn, *args, **kwargs)
            new_func.registered = True
            if 'name' in kwargs:
                new_func.__name__ = kwargs['name']
            else:
                new_func.__name__ = fn.__name__
            module_id = fn.__module__.split(".")[-1]
            new_func.module_id = module_id
            register.modules.setdefault(module_id, set()).add(new_func)
            return new_func
        return decorator

    @classmethod
    def module(cls, module_name):
        if module_name in cls.modules:
            return cls.modules[module_name]
        return None

    @classmethod
    def load_module(cls, module_name, cmds):
        """Accepts module format returned by `unload_module`"""
        cls.modules[module_name] = cmds

    @classmethod
    def unload_module(cls, module_name):
        return cls.modules.pop(module_name)

    @classmethod
    def unregister_command(cls, command):
        module = cls.modules.get(command.module_id, None)
        if module is None or command not in module:
            return False
        module.remove(command)
        return True


def require_auth(*args):
    """
    Require authorization. Can be used as a decorator or called within
    a function.
    """
    admins = config.admins  # TODO: admins, ensuring login
    def anon(bot, msg, *args):
        if msg.nick.lower() not in admins:
            return bot.reply("Auth Required.")
        return fn(bot, msg, *args)
    if len(args) == 1:  # Decorator
        fn, = args
        anon.__name__ = fn.__name__
        anon.__module__ = fn.__module__
        anon.__doc__ = fn.__doc__
        return anon
    elif len(args) == 2:  # Within-function call
        bot, msg = args
        return msg.nick in admins
    elif len(args) > 2:
        raise TypeError("require_auth() takes at most 2 arguments (%d given)" % len(args))
    raise TypeError("require_auth() takes at least 1 argument (0 given)")
