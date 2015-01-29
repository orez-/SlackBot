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


@modules.register(rule=[r"$@bot", r"([\w ]+)", r"bomb(?: (\d+))?$"])
def bomb(bot, msg, group_name, num=None):
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


@modules.register(rule=[
    r"$@bot", r"add",
    r"([\w ]+?)(?: +(?:pic|picture|image|bomb)|,)",
    r"([^ ]+)$",
])
def add_bomb(bot, msg, group_name, url):
    bomb = get_images(group_name)
    if url in bomb:
        return bot.reply("I already have that image!")
    bomb.append(url)
    save_images()
    bot.reply("Added.")


@modules.register(rule=[
    r"$@bot", r"remove",
    r"([\w ]+?)(?: +(?:pic|picture|image|bomb)|,)",
    r"([^ ]+)$",
])
def remove_bomb(bot, msg, group_name, url):
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
    bombs = get_images()
    bot.reply(", ".join(bombs))