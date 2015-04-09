# -*- coding: utf8 -*-
import modules


@modules.register(rule=r"[Hh]i $@bot!?", hide=True)
def say_hello(bot, msg):
    """
    Greet the nice people who say hello to you.
    """
    bot.reply("Hi @{}!".format(msg[u'user_name']))


high_five_regex = r"hi(?:gh)?[ -]?(?:five|5)"
@modules.register(rule=r"(?i){}[, ]*$@bot".format(high_five_regex), hide=True, priority=-5)
@modules.register(rule=r"$@bot (?i){}".format(high_five_regex), hide=True, priority=-5)
def high_five(bot, msg):
    """High five!"""
    bot.reply(":hand:")


@modules.register(rule=r"$@bot :fu:", hide=True)
def fu(bot, msg):
    """F.U.!"""
    bot.reply(
        "```\n"
        "              /´¯/)\n"
        "            ,/¯../\n"
        "           /..../ \n"
        "     /´¯/'...'/´¯¯`·¸ \n"
        "  /'/.../..../......./¨¯\ \n"
        "('(...´...´.... ¯~/'...') \n"
        " \.................'.../ \n"
        "  ''...\.......... _.·´ \n"
        "    \..............( \n"
        "      \.............\ \n"
        "```"
    )
