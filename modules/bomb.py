import collections
import random

import modules


filename = 'image_bombs'
images = None


def get_images(group_name=None):
    global images
    if images is None:
        # First time load
        version, data = modules.get_readable(filename)
        images = collections.defaultdict(list)
        if data:
            for name, urls in data.iteritems():
                if urls:
                    images[name] = urls
    if group_name:
        return images[group_name]
    return images


def save_images():
    global images
    modules.save_readable(images, filename, version=1)


def clean_images(group_name):
    if not images[group_name]:
        del images[group_name]


@modules.register(rule=[r"$@bot", r"([\w ]+)", r"bomb(?: (\d+))?$"], name="foo-bomb")
def bomb(bot, msg, group_name, num=None):
    """
    Post a deluge of pictures on the given topic.

    Optionally accepts a numeral parameter for the number of pictures
    to post.
    """
    images = get_images(group_name)
    if not images:
        bot.reply(
            "No images for {group_name}, but you can be the first to add one "
            "with `@{bot} add {group_name} pic <your url>`.".format(
                bot=bot.user_name,
                group_name=group_name)
        )
        clean_images(group_name)
    else:
        count = min(num or 5, len(images))
        bot.reply('\n'.join(random.sample(images, count)))


@modules.register(name="add-bomb", rule=[
    r"$@bot", r"add",
    r"([\w ]+?)(?: +(?:pic|picture|image|bomb)|,)",
    r"([^ ]+)$",
])
def add_bomb(bot, msg, group_name, url):
    """
    Add an image to the specified category, to be invoked with
    `@bot: [category] bomb`.
    """
    bomb = get_images(group_name)
    if url in bomb:
        return bot.reply("I already have that image!")
    bomb.append(url)
    save_images()
    bot.reply("Added.")


@modules.register(name="remove-bomb", rule=[
    r"$@bot", r"remove",
    r"([\w ]+?)(?: +(?:pic|picture|image|bomb)|,)",
    r"([^ ]+)$",
])
def remove_bomb(bot, msg, group_name, url):
    """
    Remove an image from the specified category. It will no longer
    appear with `@bot: [category] bomb`.
    """
    bomb = get_images(group_name)
    try:
        bomb.remove(url)
    except ValueError:
        bot.reply("I don't have that image about {}".format(url))
    else:
        save_images()
        bot.reply("Image removed.")
    if not bomb:
        clean_images(group_name)


@modules.register(rule=r"$@bot show bombs$")
def show_bombs(bot, msg):
    """
    Display all the different categories of image bombs.

    For more information see `foo-bomb`.
    """
    bombs = get_images()
    bot.reply(", ".join(bombs))
