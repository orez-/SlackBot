import random

import modules

filename = 'word_list'
word_list = None


def get_words(word_type):
    global word_list
    # Load the file if it has not been loaded - first load
    if word_list is None:
        version, data = modules.get_readable(filename)
        # If the file is able to be loaded
        if data:
            word_list = data
        else:
            word_list = {'adjective': [], 'noun': []}
    # Get the desired word list
    if word_type in ('adjective', 'noun'):
        return word_list[word_type]
    else:
        return None


def save_words():
    global word_list
    modules.save_readable(word_list, filename, version=1)


@modules.register(rule=[r"$@bot", r"insult", r"$(@user)"])
def insult(bot, msg, user):
    """
    Hurl insults at your teammates.
    """
    user = bot.get_nick(user)

    adjectives = get_words('adjective')
    nouns = get_words('noun')

    if nouns and adjectives:
        adjective = random.choice(adjectives)
        noun = random.choice(nouns)
        bot.reply("@{user} is {article} {adjective} {noun}".format(
            user=user,
            article="an" if adjective[0] in "aeiou" else "a",
            adjective=adjective,
            noun=noun,
        ))
    else:
        bot.reply("Shut the fuck up.")


@modules.register(rule=[r"$@bot", r"add", r"(adjective|noun)", r"([\w ,-]+)$"])
def add_word(bot, msg, word_type, word):
    """
    Add insults to the lists.
    """
    word = word.strip()

    word_list = get_words(word_type)
    if word_list is None:
        bot.reply("That part of speech is not supported.")
        return
    if word in word_list:
        bot.reply("I already have that word!")
        return
    if not word:
        bot.reply("Nice try wise guy.")
        return

    word_list.append(word)
    save_words()
    bot.reply("Added.")
