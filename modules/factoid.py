import collections
import HTMLParser
import json
import os
import re

import modules

factoids = None


class Factoid(object):
    def __init__(self, key=None, value=None, verb='is', reply=False):
        self.key = key
        self.value = value
        self.verb = verb
        self.reply = reply

    def __str__(self):
        if self.reply:
            return self.value
        return "{key} {verb} {value}".format(**self.__dict__)

    def to_json(self):
        return self.__dict__


class FactoidDatabase(collections.MutableMapping):
    def __init__(self, path):
        self._path = path
        self._db = {}
        self.load()

    def load(self):
        if not os.path.exists(self._path):
            self.flush()

        with open(self._path) as f:
            self.update([(k, Factoid(**v)) for (k, v) in json.load(f).items()])

    def flush(self):
        with open(self._path, 'wb') as f:
            json_data = dict([
                (k, factoid.to_json()) for k, factoid in self.items()
            ])
            json.dump(json_data, f)

    def _make_key(self, key):
        return key.strip().lower()

    def __contains__(self, key):
        return self._db.__contains__(self._make_key(key))

    def __getitem__(self, key):
        return self._db[self._make_key(key)]

    def __setitem__(self, key, value):
        assert isinstance(value, Factoid)
        self._db[self._make_key(key)] = value
        self.flush()

    def __delitem__(self, key):
        del self._db[self._make_key(key)]
        self.flush()

    def __iter__(self):
        return iter(self._db)

    def __len__(self):
        return len(self._db)


@modules.register(actions=['hello'], occludes=False, priority=10, threaded=True, hide=True)
def load_factoids(bot, msg):
    global factoids
    factoids = FactoidDatabase('data/factoids.json')


@modules.register(name="factoid-set", rule=r"$@bot\s+(.+)\s+(is|are)\s+(.+)")
def set_factoid(bot, msg, key, verb, value):
    """
    Set a factoid. Invoked with `@bot: [key] is [value]` or
    `@bot: [key] are value`. You can also use the form
    `@bot: [key] is <reply>[value]` to have the bot respond with only the
    value instead of repeating "[key] is".
    """
    value = HTMLParser.HTMLParser().unescape(value)
    factoid = Factoid(key=key, verb=verb, value=value, reply=False)

    if value.startswith('<reply>'):
        factoid.value = re.sub('^<reply>\s*', '', value)
        factoid.reply = True

    factoids[key] = factoid
    bot.reply('ok')


@modules.register(name="factoid-get", rule=r"(.+)[!?]", priority=-10)
def get_factoid(bot, msg, key):
    """
    Get a factoid. Invoked with `foo?` or `foo!` for a factoid named foo.
    """
    if key in factoids:
        bot.reply(factoids[key])


@modules.register(name="factoid-forget", rule=r"$@bot\s+forget\s+(.+)")
def forget_factoid(bot, msg, key):
    """
    Forget a factoid. Invoked with `@bot: forget foo` for a factoid named foo.
    """
    try:
        del factoids[key]
        bot.reply('ok')
    except KeyError:
        bot.reply('no factoid named {key}'.format(key))
