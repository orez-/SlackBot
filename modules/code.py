import re
import requests

import exception
import modules
import util


supported_languages = {
    'c++': 'c++/c++11-gcc-4.9.1',
    'coffeescript': 'coffeescript/node-0.10.29-coffee-1.7.1',
    'fortran': 'fortran/f95-4.4.3',
    'gcc': 'c/gcc-4.9.1',
    'haskell': 'haskell/hugs98-sep-2006',
    'javascript': 'javascript',
    'lua': 'lua/lua-5.2.3',
    'ocaml': 'ocaml/ocaml-4.01.0',
    'pascal': 'pascal/fpc-2.6.4',
    'perl': 'perl/perl-5.20.0',
    'php': 'php/php-5.5.14',
    'python': 'python/cpython-2.7.8',
    'py3': 'python/cpython-3.4.1',
    'ruby': 'ruby/mri-2.2',
    'x86': 'assembly/nasm-2.07',
}

languages_regex = '|'.join(map(re.escape, supported_languages))


@modules.register(rule=r"$@bot\s+({languages})\s+((?:`(?:``)?)?)(.*)\2".format(
    languages=languages_regex), threaded=True)
def code(bot, msg, language, _, code):
    """
    Run arbitrary code of the specified language.

    Usage:
      @you: @bot python `print [x ** 2 for x in xrange(10) if x % 2]`
      @bot: [1, 9, 25, 49, 81]

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
    bot.debug(response.url)
    _, html = response.content.split("<h2>Program Output</h2>", 1)
    html = html.lstrip()
    html = html[5: html.index("</pre>")]
    output = util.unescape(html).rstrip().decode('utf-8')
    if output:
        try:
            bot.reply(u"```{}```".format(output))
        except exception.MessageTooLongException:
            bot.reply(response.url)
    else:
        bot.reply("No output...")
