"""
Util for threading bot commands.
"""

import functools
import threading


threads = []


def join_threads():
    """
    Wait for threaded commands to clean themselves up.

    This is achieved by requesting each of them to stop, then waiting
    until each of them has stopped. It is the thread's responsibility
    to stop in a timely manner.
    """
    _threads = threads[:]
    for thread in _threads:
        thread.stop()
    for thread in _threads:
        thread.join()


def _register(thread, target):
    """
    Track a StoppableThread, and make its target function clean up after
    itself when it exits.
    """
    threads.append(thread)

    @functools.wraps(target)
    def deregister(*args, **kwargs):
        try:
            return target(*args, **kwargs)
        finally:
            try:
                threads.remove(thread)
            except:  # I honestly do not care.
                pass
    return deregister


class StoppableThread(threading.Thread):
    def __init__(self, target, *args, **kwargs):
        self._target = _register(self, target)
        super(StoppableThread, self).__init__(target=self._target, *args, **kwargs)
        self._stopped = threading.Event()

    def stop(self):
        self._stopped.set()

    def stopped(self):
        return self._stopped.is_set()

    def __str__(self):
        return self._target.__name__
