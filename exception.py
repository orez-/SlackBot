class SlackbotException(Exception):
    """
    Generic SlackBot exception super class.
    """


class MessageTooLongException(SlackbotException):
    """
    Tried to send a message that was too long from SlackBot.
    """
