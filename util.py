"""
Module containing utility functions and classes.
"""

# Standard library modules
import datetime
import os
import Queue
import time

class CustomQueue(Queue.Queue):
    """
    Subclass of Queue.Queue to provide the ability to add an item to the front
    of a queue. This is useful when an item is taken from the queue but an
    error occurs when processing the item. If processing may continue at a
    later time then the item should be put at the front of the queue until
    processing is resumed.
    """
    def put(self, item, block=True, timeout=None, front=False):
        """
        To put an item at the front of the queue use:
        my_queue.put(item, front=True)
        """
        self.not_full.acquire()
        try:
            if not block:
                if self._full():
                    raise Full
            elif timeout is None:
                while self._full():
                    self.not_full.wait()
            else:
                if timeout < 0:
                    raise ValueError("'timeout' must be a positive number")
                endtime = _time() + timeout
                while self._full():
                    remaining = endtime - _time()
                    if remaining <= 0.0:
                        raise Full
                    self.not_full.wait(remaining)
            if front:
                self.queue.appendleft(item)
            else:
                self.queue.append(item)
            self.unfinished_tasks += 1
            self.not_empty.notify()
        finally:
            self.not_full.release()


def get_http_expiry(days):
    """
    Adds the given number of days on to the current date and returns the future
    date as a string, in the format: "Mon, 18 Jan 2010 17:10:02 GMT"
    """
    expire_date = datetime.datetime.now() + datetime.timedelta(days=days)
    return expire_date.strftime('%a, %d %b %Y %H:%M:%S GMT')


def get_modified_datetime(filename):
    """
    Returns the date and time that a file was last modified, as a string, in
    the format: "Mon, 18 Jan 2010 17:10:02 GMT"
    """
    timestamp = time.localtime(os.path.getmtime(filename))
    modified_date = datetime.datetime(*timestamp[:-2])
    return modified_date.strftime('%a, %d %b %Y %H:%M:%S GMT')


def secs_from_days(days):
    """
    Returns the number of seconds that are in the given number of days.
    (i.e. 1 returns 86400)
    """
    return 86400 * days
