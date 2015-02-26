import functools
import inspect
import json
import re
import threading
import time


def valid_regex(regex):
    try:
        re.compile(regex)
    except re.error:
        return False
    else:
        return True

UNSET = object()


class BotCommand(object):
    RULE_VERSION = 0

    def __init__(
            self, fn,
            rule=UNSET, actions=["message"], priority=0, sender=None,
            ttl=False, activations=False, name=None, threaded=False,
            hide=False, occludes=True, occludable=True, fields=None):
        """
        TODO: This needs documentation like real badly.
        """
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

        self.threaded = threaded
        self.hide = hide
        self.occludes = occludes
        self.occludable = occludable
        self.fields = fields or {}
        functools.update_wrapper(self, fn)

    @property
    def sender(self):
        """
        Get the regex that matches sender on which to trigger.
        If the regex does not exist, generates it.
        """
        if self._compiled_sender is None:
            if isinstance(self._sender, basestring):
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

        $bot - Bot nick
        $@bot - Bot ping
        """
        if self._rule is UNSET:
            return UNSET
        if self._compiled_rule is None or self._rule_version != BotCommand.RULE_VERSION:
            if self._rule is None:
                rule = r".*"
            elif isinstance(self._rule, basestring):
                rule = self._rule
            elif isinstance(self._rule, list):
                rule = r'\s+'.join(self._rule)
            else:
                raise ValueError("invalid rule format")

            for keyword, replacement in [
                    (r"$bot", self.bot.user_name),
                    (r"$@bot", r"<@{}>:?".format(self.bot.user)),
                    (r"$yes", r"(?:yes|yup|yeah|uh huh)"),
                    (r"$no", r"(?:nope|no|nah|nuh uh)"),
                    (r"$@user", r"<@U\w+>:?"),
                    (r"$(@user)", r"<@(U\w+)>:?")]:
                rule = rule.replace(keyword, replacement)

            self._rule_version = BotCommand.RULE_VERSION
            self._compiled_rule = re.compile(rule, re.DOTALL)
        return self._compiled_rule

    def matches(self, bot, msg):
        """Determine if the given message should trigger this command."""
        # If action is PING sender is None, safe to fall through.
        # if not (msg.sender is None or self.sender.match(msg.sender)):
        #     return False
        self.bot = bot
        if msg.get('type') not in self.actions:
            return False
        if self.occludable and u'occluded' in msg:
            return False
        if self.fields:
            for name, value in self.fields.iteritems():
                if name not in msg:
                    return False
                if msg[name] != value and value is not any:
                    return False
        if self.rule is not UNSET:
            if u'text' not in msg:
                return False
            return self.rule.match(msg[u'text'])
        return re.match("", "")

    def __call__(self, bot, msg, *args):
        """Run the command's function."""
        if self.activations:
            self.activations -= 1
        if self.occludes:
            msg[u'occluded'] = True
        if self.threaded:
            t = threading.Thread(target=self._fn, args=(bot, msg) + args)
            t.setDaemon(True)
            t.start()
        else:
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
                new_func.name = kwargs['name']
            else:
                new_func.name = new_func.__name__.replace('_', ' ').strip()
            new_func.full_help = inspect.getdoc(new_func)
            new_func.help = None
            if new_func.full_help is not None:
                new_func.help = new_func.full_help.split("\n\n", 1)[0]
            module_id = fn.__module__.split(".")[-1]
            new_func.module_id = module_id
            register.modules.setdefault(module_id, set()).add(new_func)
            return fn
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

# ===
# Data methods
readable_path = 'data/{}.json'


def save_readable(obj, filename, version):
    with open(readable_path.format(filename), 'w') as f:
        json.dump({'version': version, 'data': obj}, f)


def get_readable(filename):
    try:
        with open(readable_path.format(filename)) as f:
            result = json.load(f)
        return result['version'], result['data']
    except IOError:
        return None, None
