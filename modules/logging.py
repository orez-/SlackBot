"""
Bot module to handle bookkeeping on the bot object itself, based on
messages received from Slack.
"""

import modules

MAX_LOGS = 30


@modules.register(
    actions=[None], fields=dict(reply_to=any), priority=20, hide=True, occludes=False)
def acknowledge_received(bot, msg):
    """
    Acknowledge the server's acknowledgement of message delivery.

    When a Slack client sends a message to the server, it is sent a
    confirmation message back that the message was received.

    This function assures the message was not somehow in error,
    and logs the message in a short queue of the bot's recent messages.
    """
    try:
        old_msg = bot.pending_outgoing_messages.pop(msg[u'reply_to'])
    except KeyError:  # Fine, who needs ya.
        return
    if not msg[u'ok']:
        bot.debug(msg[u'error'])
        return

    msg[u'channel'] = old_msg[u'channel']
    bot.previous_messages.appendleft(msg)
    for _ in xrange(len(bot.previous_messages) - MAX_LOGS):
        bot.previous_messages.pop()


@modules.register(actions=['team_join', 'user_change'], hide=True, occludes=False)
def update_user(bot, msg):
    """
    When a user joins the team, the bot needs to know about them so it
    can respond appropriately.
    """
    user = msg[u'user']
    bot.users[user[u'id']] = user


@modules.register(actions=['im_open'], hide=True, occludes=False)
def im_open(bot, msg):
    """
    When a direct message channel has been opened between the bot and
    another user, the bot needs to know that that's the correct way to
    private message them.
    """
    bot.users[msg[u'user']][u'im'] = msg[u'channel']


@modules.register(actions=['im_close'], hide=True, occludes=False)
def im_close(bot, msg):
    """
    When a direct message channel has been closed between the bot and
    another user, the bot needs to know that that's no longer an option
    private message them.
    """
    bot.users[msg[u'user']][u'im'] = None


@modules.register(rule=[r"$@bot", r"redact"])
def redact(bot, msg):
    """
    Remove the text of the bot's previous message in this channel.
    """
    last_msg = next((m for m in bot.previous_messages if m[u'channel'] == msg[u'channel']), None)
    if not last_msg:
        return
    bot.edit_message(
        timestamp=last_msg[u'ts'],
        channel=msg[u'channel'],
        new_text='REDACTED',
    )
