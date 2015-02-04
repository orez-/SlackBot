import modules


@modules.register(rule=r'$@bot (?:help|commands) *$')
def commands(bot, msg):
    bot.reply("Available commands: {}".format(', '.join(
        cmd.name
        for cmd in bot.commands
        if not cmd.hide
    )))


@modules.register(rule=r'$@bot help (\w.*)', priority=-10)
def help(bot, msg, query):
    """
    Get a short blurb of information about a command. For more in-depth
    information, see the `man` command.
    """
    command = next((cmd for cmd in bot.commands if cmd.name == query and not cmd.hide), None)
    if not command:
        bot.reply("I don't recognize that command.")
        return
    elif not command.help:
        bot.reply("No helpful information provided for this command.")
        return
    bot.reply(command.help)


@modules.register(rule=r'$@bot man(?: (\w.*))?', priority=-10)
def man(bot, msg, query):
    """
    Get the full documentation for a command.

    For a quicker snapshot of a command's functionality, see the
    `help` command.
    """
    if query is None:
        bot.reply("Usage: `@{bot}: man [command]`".format(bot=bot.user_name))
        return
    command = next((cmd for cmd in bot.commands if cmd.name == query and not cmd.hide), None)
    if not command:
        bot.reply("I don't recognize that command.")
        return
    elif not command.full_help:
        bot.reply("No helpful information provided for this command.")
        return
    bot.reply(command.full_help)
