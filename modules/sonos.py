# -*- coding: utf8 -*-

import collections
import functools

import soco

import modules


groups = collections.defaultdict(list)
coordinator = None


def _sonos_refresh():
    global coordinator
    groups.clear()
    speakers = soco.discover()
    if speakers:
        for speaker in speakers:
            groups[speaker.group.coordinator].append(speaker)
    coordinator = None if len(groups) != 1 else groups.keys()[0]
    return bool(speakers)


_sonos_refresh()


def play_state(speaker):
    """
    Get the state of the speaker.

    Valid values include PLAYING, PAUSED_PLAYBACK, STOPPED, TRANSITIONING
    """
    return speaker.get_current_transport_info()['current_transport_state']


def format_track_info(speaker):
    track_info = speaker.get_current_track_info()
    state = play_state(speaker)
    return ("{action} {song} by {artist}.".format(
        song=track_info[u'title'],
        artist=track_info[u'artist'],
        action={
            'PLAYING': 'Now playing',
            'TRANSITIONING': 'Now playing',
            'PAUSED_PLAYBACK': 'Paused:',
            'STOPPED': 'Up next:',
        }.get(state, state)
    ))


def get_speaker(fn):
    """
    Decides upon and passes a Sonos speaker to the wrapped function.

    The chosen speaker is the globally assigned coordinator. If none
    is assigned, responds to chat with an error message and some steps
    to take to remedy.

    The wrapped function will also gracefully catch and report
    Sonos errors.
    """
    @functools.wraps(fn)
    def anon(bot, msg, *args, **kwargs):
        global coordinator
        if not groups:
            bot.reply("Could not find a Sonos system on the network.")
            return
        if coordinator:
            speaker = coordinator.group.coordinator
        else:
            bot.reply(
                "Multiple sets of speakers found on the network! Choose "
                "a speaker set to control with `{bot} sonos set speaker "
                "[speaker name]`. To see a list of available speakers, "
                "use `{bot} sonos topology`.".format(bot=bot.user_name)
            )
            return
        try:
            return fn(bot, msg, speaker, *args, **kwargs)
        except soco.SoCoException:
            bot.reply("Error interfacing with Sonos ...")
            raise
    return anon


@modules.register(rule=r"$@bot sonos previous")
@get_speaker
def sonos_previous(bot, msg, speaker):
    """
    Play the previous song in the queue on the Sonos system.
    """
    speaker.previous()
    bot.reply(format_track_info(speaker))


@modules.register(rule=r"$@bot sonos (?:next|skip)")
@get_speaker
def sonos_next(bot, msg, speaker):
    """
    Play the next song in the queue on the Sonos system.
    """
    speaker.next()
    bot.reply(format_track_info(speaker))


@modules.register(rule=r"$@bot sonos play *$")
@get_speaker
def sonos_play(bot, msg, speaker):
    """
    Resume playback of the current song in the queue on the
    Sonos system.
    """
    speaker.play()
    bot.reply(format_track_info(speaker))


@modules.register(rule=r"$@bot sonos pause")
@get_speaker
def sonos_pause(bot, msg, speaker):
    """
    Pause playback of the current song in the queue on the Sonos system.
    """
    speaker.pause()


@modules.register(rule=r"$@bot sonos stop")
@get_speaker
def sonos_stop(bot, msg, speaker):
    """
    Stop playback of the Sonos system.
    """
    speaker.stop()


@modules.register(rule=r"$@bot sonos refresh")
def sonos_refresh(bot, msg):
    """
    Attempt to discover updates to the Sonos speaker topology.
    """
    _sonos_refresh()
    bot.reply(format_topology())


@modules.register(rule=r"$@bot sonos (?:track|info)")
@get_speaker
def sonos_track(bot, msg, speaker):
    """
    Display information about the current track on the Sonos system.
    """
    bot.reply(format_track_info(speaker))


@modules.register(rule=r"$@bot sonos topology")
def sonos_topology(bot, msg):
    """
    Display a visual representation of the Sonos speaker configuration.

    Speaker configuration may be displayed something like:
      Kitchen
    ⇒ ├ Toaster
      └ Cupboard
      Living Room
      └ TV

    This example denotes two groups of speakers, coordinated by the
    speakers Kitchen and Living Room. The arrow represents the speaker
    and speaker group on which the bot's commands will take action.
    """
    bot.reply(format_topology())


@modules.register(rule=r"$@bot sonos set speaker (.+)")
def sonos_set_speaker(bot, msg, speaker_name):
    """
    Tell the bot which speaker to interact with in further commands.

    For the most part any speaker in a speaker group can be used
    interchangably to control song playback. Volume controls however
    may be per-speaker.

    To see a full list of speakers to choose from, do
    `@bot sonos topology`.
    """
    global coordinator
    speaker_name = speaker_name.lower()
    for group in groups.itervalues():
        for speaker in group:
            if speaker._player_name.lower() == speaker_name:
                coordinator = speaker
                bot.reply(u"Speaker set to {}.".format(speaker._player_name))
                return
    bot.reply(
        "Could not find a speaker with that name. To see a full list of "
        "speakers on my network, try `@{bot} sonos topology`. If you're "
        "sure the speaker's connected but I'm not aware of it, try "
        "`@{bot} sonos refresh`.".format(bot=bot.user_name)
    )


def format_topology():
    global coordinator
    if not groups:
        return "Could not find a Sonos system on the network."
    lines = collections.deque()
    for s_coordinator, speakers in groups.iteritems():
        lines.append(
            (u"⇒ {}" if s_coordinator == coordinator else u"  {}")
            .format(s_coordinator._player_name)
        )
        for i, speaker in enumerate(s for s in speakers if s != s_coordinator):
            lines.append(
                (u"{} └ {}" if i == len(speakers) - 2 else u"{} ├ {}").format(
                    u"⇒" if speaker == coordinator else u" ",
                    speaker._player_name))
    return u"```{}```".format('\n'.join(lines))
