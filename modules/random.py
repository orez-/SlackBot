import bisect
import collections
from math import log as ln, pi, e
import random
import re
import time

import modules
import util

TERMS_CUTOFF = 10
DICE_CUTOFF = 100000
RESULTS_CUTOFF = 10


def _quadratic(a, b, c):
    d = (b * b - 4 * a * c) ** .5
    return ((-b - d) / (2 * a), (-b + d) / (2 * a))


def _probabilistic_sum(number_of_dice, sides):
    """
    For inordinately large numbers of dice, we can approximate their
    sum by picking a random point under the bell-curve that represents
    the probabilistic sums.

    We accomplish this by picking a random y value on the curve, then
    picking a random x value from the bounds of that y intercept.
    """
    n = number_of_dice
    s = sides
    u = ((s + 1.) / 2) * n  # mean
    B = (1.7 * (n ** .5) * ((2 * pi) ** .5))
    max_y = 1. / B
    min_y = (e ** ((-(n - u) ** 2) / (2 * 1.7 * 1.7 * n))) / B
    Y = random.uniform(min_y, max_y)

    try:
        T = ln(Y * B) * (2 * (1.7 * 1.7) * n)
    except ValueError:
        # Too close to 0, rounding off
        T = 0
        min_x, max_x = n, n * s
    else:
        min_x, max_x = _quadratic(1, -2 * u, T + u ** 2)
    return int(round(random.uniform(min_x, max_x)))


@modules.register(rule=r'^(?:[1-9]\d*)?d[1-9]\d*(?:\s?[\+\-]\s?(?:[1-9]\d*)?d[1-9]\d*)*$')
def dice(bot, message):
    """
    Get the sum of rolled dice in the format [k]d[n],
    where k is the number of dice and n is the number of sides.
    """
    rest = message['text'].replace(" ", "")  # remove all whitespace
    results = []
    total = 0
    terms = 0
    if rest.count("+") + rest.count("-") >= TERMS_CUTOFF:
        return
    try:
        while rest:
            terms += 1
            mult, how_many, sides, rest = re.match(r"([\+\-]?)(\d*)d(\d+)(.*)", rest).groups()
            mult = -1 if mult == "-" else 1
            if not how_many:
                how_many = 1
            how_many = int(how_many)
            sides = int(sides)
            if results is False or how_many > DICE_CUTOFF:  # shortcut
                results = False
                total += _probabilistic_sum(how_many, sides)
            else:
                results = [random.randint(1, sides) for _ in xrange(how_many)]
                total += sum(results) * mult
        if terms == 1 and results:
            if 1 < len(results) <= RESULTS_CUTOFF:
                bot.reply(', '.join(map(str, results)) + ". Total: " + str(total))
                return
        bot.reply(str(total))
    except OverflowError:
        bot.reply("Calm down bro.")


class SequenceList(object):
    """
    Container for a list of sequences meant to be accessed as a
    flat list, without necessarily expanding the sequences.

    Although it is not enforced, the subsequences should be considered
    immutable.

    Example:
    >>> sl = SequenceList()
    >>> sl.add(xrange(97))
    >>> sl.add(["ninety-seven", "ninety-eight", "ninety-nine"])
    >>> sl.add(xrange(99999999999999))
    >>> print sl[6], sl[98], sl[5403]
    6 ninety-eight 5303
    """
    def __init__(self):
        self.len = 0
        self.list = []

    def __len__(self):
        return self.len

    def __getitem__(self, index):
        if index < 0:
            raise IndexError
        for elem in self.list:
            if index >= len(elem):
                index -= len(elem)
            else:
                return elem[index]
        raise IndexError

    def __iter__(self):
        for subsequence in self.list:
            for elem in subsequence:
                yield elem

    def append(self, value):
        self.list.append([value])
        self.len += 1

    def extend(self, sequence):
        self.list.append(sequence)
        self.len += len(sequence)


def _parse_shuffle_set(bot, shuffle_string):
    """
    Parse a sequence definition for `shuffle` and `choose`.

    Sequence definition syntax is covered in `shuffle`.
    """
    shuffle_string = shuffle_string.strip()
    shuffle_list = shuffle_string.split()
    if len(shuffle_list) > 1:
        return True, shuffle_list
    shuffle_components = shuffle_string.split(',')
    error_list = []
    shuffle_list = SequenceList()
    for elem in shuffle_components:
        one, is_range, two = elem.partition(':')
        if is_range:
            try:
                one = int(one)
                two = int(two)
            except ValueError:
                error_list.append("{}: invalid range.".format(elem))
            else:
                if one > two:
                    error_list.append(
                        "{}: first digit must not be larger than second.".format(elem))
                else:
                    shuffle_list.extend(xrange(one, two + 1))
            continue
        elif elem in ("<!channel>", "<!group>"):
            # If you're currently in a channel, consider this a range
            # of all people in that channel.
            if bot.channel:
                shuffle_list.extend([
                    "@{}".format(bot.get_nick(uid))
                    for uid in bot.channel[u'members']
                ])
                continue
            # If you're not, treat it like any other string.
            else:
                elem = "@{}".format(elem[2:-1])

        if len(shuffle_components) == 1:
            # If this word the only element, use its characters.
            shuffle_list.extend(elem)
        else:
            shuffle_list.append(elem)

    if error_list:
        return False, error_list
    return True, shuffle_list


@modules.register(rule=[r"$@bot", r"shuffle", r"(.+)$"])
def shuffle(bot, msg, shuffle_string):
    """
    Given a sequence definition, return the elements of that sequence
    in a random order.

    Note that if the sequence is over 200 elements, only the first 200
    will be shown.

    A sequence is generated by the following rules:
    1. If the sequence definition contains spaces the spaces are
       considered a delimiter and each of the tokens is considered
       literally.

       Example:
       @you: @bot shuffle four score and seven years ago
       @bot: years, seven, four, ago, score, and

    2. Otherwise, commas are used as the delimiter. Each comma delimited
       element is interpreted as follows:
       i. Two integers of the format ``a:b`` are a range from ``a``
           to ``b``, inclusive.
       ii. The @channel mention, if in a channel, is expanded as the
           nick of every person in the channel. Note that since spaces
           are disallowed the @channel mention must come first.
       iii. A literal string. If a literal string is the only
            comma-delimited element it is interpreted as its characters.

       Example:
       @you: @bot shuffle @channel,4:6,word
       @bot: 5, @you, 6, @bot, word, 4

       @you: @bot shuffle exemplify
       @bot: l, f, i, m, x, p, y, e, e
    """
    CUTOFF = 200
    shuffle_string = util.flatten_incoming_text(bot, shuffle_string, flatten_notice=False)
    success, shuffle_list = _parse_shuffle_set(bot, shuffle_string)
    if not success:
        bot.reply('\n'.join(shuffle_list))
        return
    shuffle_list = random.sample(shuffle_list, min(len(shuffle_list), CUTOFF))
    bot.reply(" " + ", ".join(map(str, shuffle_list)))


@modules.register(rule=[r"$@bot", r"choose", r"(.+)$"])
def choose(bot, msg, choose_string):
    """
    Given a sequence definition, return an element at random from that
    sequence.

    Sequence definition syntax is detailed in `shuffle`.
    """
    choose_string = util.flatten_incoming_text(bot, choose_string, flatten_notice=False)
    success, choose_list = _parse_shuffle_set(bot, choose_string)
    if not success:
        bot.reply('\n'.join(choose_list))
        return
    bot.reply(" {}".format(random.choice(choose_list)))


# ===
# Markov chain stuff.

class MarkovData(object):
    _data = {}

    def __init__(self, token):
        self.token = token
        self._next_tokens = []
        self._next_odds = []
        type(self)._data[token] = self

    def random_token(self):
        ishdex = random.randint(0, self._next_odds[-1])
        index = bisect.bisect_left(self._next_odds, ishdex)
        return type(self).get(self._next_tokens[index])

    def add_next_token(self, token, probability):
        self._next_tokens.append(token)
        if self._next_odds:
            probability += self._next_odds[-1]
        self._next_odds.append(probability)

    def __nonzero__(self):
        return bool(self.token)

    @classmethod
    def get(cls, token):
        return cls._data[token]


def get_markov_generator(filename):
    token_list = collections.defaultdict(collections.Counter)

    class cls(MarkovData):
        _data = {}

    print "Parsing data from file..."
    try:
        with open(filename) as f:
            for line in f:
                line = line[line.index("\t") + 1:].split()
                for word, next_word in zip([None] + line, line + [None]):
                    token_list[word][next_word] += 1
    except IOError:
        print "Could not open file {}.".format(filename)
        markov = False
        return
    print "Parsed data, formatting..."
    for text, next_tokens in token_list.iteritems():
        token = cls(text)
        for next_text, probability in next_tokens.iteritems():
            token.add_next_token(next_text, probability)
    print "Formatted!"

    def markov():
        token = cls.get(None).random_token()
        while token:
            yield token.token
            token = token.random_token()
    return lambda: u' '.join(markov())


markov = None


@modules.register(actions=['hello'], occludes=False, priority=10, threaded=True, hide=True)
def load_markov(bot, msg):
    global markov
    markov = get_markov_generator('data/hugs.final')


@modules.register(rule=r"$@bot wtf", name="wtf")
def group_hug(bot, msg):
    t = time.time()
    while markov is None and time.time() < t + 3:
        time.sleep(0.5)
    if markov:
        bot.reply(u"> {}".format(markov()))
    else:
        bot.reply("Could not load training set.")
