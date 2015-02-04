import modules


@modules.register(rule=r"[Hh]i $@bot!?", hide=True)
def say_hello(bot, msg):
    """
    Greet the nice people who say hello to you.
    """
    bot.reply("Hi @{}!".format(msg[u'user_name']))
