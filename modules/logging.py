import modules

MAX_LOGS = 30


@modules.register(actions=[None], fields=dict(reply_to=any))
def acknowledge_received(bot, msg):
    try:
        old_msg = bot.pending_outgoing_messages.pop(msg[u'reply_to'])
    except KeyError:  # Fine, who needs ya.
        return
    if not msg[u'ok']:
        print msg[u'error']
        return

    msg = dict(msg)
    msg[u'channel'] = old_msg[u'channel']
    bot.previous_messages.appendleft(msg)
    for _ in xrange(len(bot.previous_messages) - MAX_LOGS):
        bot.previous_messages.pop()


@modules.register(rule=[r"$@bot", r"redact"])
def redact(bot, msg):
    last_msg = next((m for m in bot.previous_messages if m[u'channel'] == msg[u'channel']), None)
    if not last_msg:
        return
    # TODO: make this a method, rather than constructing a raw websocket packet.
    bot._slack_api.send_web('chat.update', dict(
        ts=last_msg[u'ts'],
        channel=msg[u'channel'],
        text='REDACTED',
    ))
