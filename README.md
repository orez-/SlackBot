# SlackBot
A bot to interface with Slack. It's still like crazy rough!

## Setup
Setup's probably the jenkiest part of this whole operation still!

1. Clone this repo locally.
2. Create a file `config.py` at the root of SlackBot. It should define the locals `default_channel` as the default channel to communicate with, and `token` as the bot token of the Slack team you want to interface with.

 ```python
 token = "MyToken"
 default_channel = "#general"
 ```
3. `python bot.py`

Optional: for tab completion in OSX run `[sudo] pip install readline`.

## Creating Modules
This section could use a full writeup someday. An extremely basic example can be found in [modules/friendly.py](https://github.com/orez-/SlackBot/blob/master/modules/friendly.py)
