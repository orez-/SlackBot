from math import log as ln, pi, e
import random
import re

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


def _parse_shuffle_set(bot, shuffle_string):
    CUTOFF = 200

    shuffle_string = shuffle_string.strip()
    shuffle_list = shuffle_string.split()
    if len(shuffle_list) > 1:
        return True, shuffle_list
    shuffle_list = shuffle_string.split(',')
    error_list = []
    total_length = len(shuffle_list)
    for i, elem in enumerate(shuffle_list):
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
                    total_length += two - one
                    if total_length > CUTOFF:
                        error_list.append("Too many elements ( > {}).".format(CUTOFF))
                        break
                    shuffle_list[i] = range(one, two + 1)
            continue
        elif elem in ("<!channel>", "<!group>"):
            # If you're currently in a channel, consider this a range
            # of all people in that channel.
            if bot.channel:
                total_length += len(bot.channel[u'members']) - 1
                if total_length > CUTOFF:
                    error_list.append("Too many elements ( > {}).".format(CUTOFF))
                    break
                shuffle_list[i] = ["@{}".format(bot.get_nick(uid)) for uid in bot.channel[u'members']]
                continue
            # If you're not, treat it like any other string.
            else:
                shuffle_list[i] = "@{}".format(elem[2:-1])

        if len(shuffle_list) != 1:
            shuffle_list[i] = [elem]
    if error_list:
        return False, error_list
    return True, [x for lst in shuffle_list for x in lst]


@modules.register(rule=[r"$@bot", r"shuffle", r"(.+)$"])
def shuffle(bot, msg, shuffle_string):
    shuffle_string = util.flatten_incoming_text(bot, shuffle_string, flatten_notice=False)
    success, shuffle_list = _parse_shuffle_set(bot, shuffle_string)
    if not success:
        bot.reply('\n'.join(shuffle_list))
        return
    random.shuffle(shuffle_list)
    bot.reply(" " + ", ".join(map(str, shuffle_list)))


@modules.register(rule=[r"$@bot", r"choose", r"(.+)$"])
def choose(bot, msg, choose_string):
    choose_string = util.flatten_incoming_text(bot, choose_string, flatten_notice=False)
    success, choose_list = _parse_shuffle_set(bot, choose_string)
    if not success:
        bot.reply('\n'.join(choose_list))
        return
    bot.reply(" {}".format(random.choice(choose_list)))


if __name__ == '__main__':
    print __doc__.strip()
