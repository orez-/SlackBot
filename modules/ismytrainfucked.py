 # -*- coding: utf8 -*-
from bs4 import BeautifulSoup
import requests

import modules


@modules.register(rule=r"$@bot are the trains fucked\?")
def are_the_trains_fucked(bot, msg):
    """
    Respond with the latest from ismytrainfucked.com

    """
    url = 'http://ismytrainfucked.com'
    result = requests.get(url)
    train_status = BeautifulSoup(result.text).pre.text
    if train_status:
        # remove the 'source on github' from response
        train_status = '\n'.join(train_status.split('\n')[:-2])
        bot.reply("```{}```".format(train_status))
    else:
        bot.reply("¯\_(ツ)_/¯")
