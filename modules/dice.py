from math import log as ln, pi, e
import random
import re

import modules

TERMS_CUTOFF = 10
DICE_CUTOFF = 100000
RESULTS_CUTOFF = 10


def quadratic(a, b, c):
    d = (b * b - 4 * a * c) ** .5
    return ((-b - d) / (2 * a), (-b + d) / (2 * a))


def probabilistic_sum(number_of_dice, sides):
    n = number_of_dice
    s = sides
    u = ((s + 1.) / 2) * n  # mean
    B = (1.7 * (n ** .5) * ((2 * pi) ** .5))
    max_y = 1. / B
    min_y = (e ** ((-(n - u) ** 2) / (2 * 1.7 * 1.7 * n))) / B
    Y = random.uniform(min_y, max_y)

    try:
        T = ln(Y * B) * ((2 * (1.7 * 1.7) * n))
    except ValueError:
        # Too close to 0, rounding off
        T = 0
        min_x, max_x = n, n * s
    else:
        min_x, max_x = quadratic(1, -2 * u, T + u ** 2)
    return int(round(random.uniform(min_x, max_x)))


@modules.register(rule=r'^(?:[1-9]\d*)?d[1-9]\d*(?:\s?[\+\-]\s?(?:[1-9]\d*)?d[1-9]\d*)*$')
def dice(bot, message):
    """Gets the sum of rolled dice in the format [k]d[n]. Rolls k dice with n sides."""
    msg = message['text']
    rest = msg.replace(" ", "")  # remove all whitespace
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
                total += probabilistic_sum(how_many, sides)
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


if __name__ == '__main__':
    print __doc__.strip()
