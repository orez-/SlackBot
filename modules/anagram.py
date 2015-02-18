 # -*- coding: utf8 -*-
import re
import requests
import urllib

import modules


@modules.register(rule=r"$@bot anagram (.+)")
@modules.register(rule=r"$@bot nag a ram (.+)", hide=True)
def anagram(bot, msg, to_anagram):
    """
    Respond with a clever anagram of the given text.

    Inspired by Sternest Meanings, powered by Anagram Genius.
    """
    to_anagram = urllib.quote(to_anagram.encode('utf8'), '')
    query = 'http://www.anagramgenius.com/server.php?source_text={}'.format(to_anagram)
    result = requests.get(query)
    # Hooray pre-RESTful internet
    anagram = re.search(
        r"<br><span class=\"black-18\">'(.*)'</span></h3>",
        result.text,
    )
    if anagram:
        bot.reply(anagram.group(1))
    else:
        bot.reply(u"¯\_(ツ)_/¯")
