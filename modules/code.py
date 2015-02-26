import requests

import exception
import modules
import util


supported_languages = {
    'python': 'python/cpython-2.7.8',
    'py3': 'python/cpython-3.4.1',
    'ruby': 'ruby/mri-2.2',
    'coffeescript': 'coffeescript/node-0.10.29-coffee-1.7.1',
    'gcc': "c/gcc-4.9.1",
    'php': "php/php-5.5.14",
}


@modules.register(rule=r"$@bot ({languages}) ((?:`(?:``)?)?)(.*)\2".format(
    languages='|'.join(supported_languages)), threaded=True)
def code(bot, msg, language, _, code):
    """
    Run arbitrary code of the specified language.

    Usage:
    ```
      @bot python `print [x ** 2 for x in xrange(10) if x % 2]`
      [1, 9, 25, 49, 81]
    ```

    Valid languages include python, py3, ruby, coffeescript, gcc (C),
    and php.
    """
    uri = 'https://eval.in/'
    data = {
        "utf8": "\xce\xbb",
        "execute": "on",
        "private": "on",
        "lang": supported_languages[language],
        "input": "",
        "code": util.flatten_incoming_text(bot, code).encode('utf-8'),
    }
    response = requests.post(uri, data)
    print response.url
    _, html = response.content.split("<h2>Program Output</h2>", 1)
    html = html.lstrip()
    html = html[5: html.index("</pre>")]
    output = util.unescape(html).rstrip()
    if output:
        try:
            bot.reply("```{}```".format(output))
        except exception.MessageTooLongException:
            bot.reply(response.url)
    else:
        bot.reply("No output...")
