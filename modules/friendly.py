import modules


@modules.register(rule=r"[Hh]i frankling(?:-)?")
def say_hello(bot, msg):
    bot.reply("Hi {}!".format(msg[u'user_name']))
