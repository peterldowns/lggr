# coding: utf-8
import sys
import time
import Queue
import threading
import multiprocessing

def coroutine(func):
    """ Decorator for priming co-routines that use (yield) """
    def wrapper(*args, **kwargs):
        c = func(*args, **kwargs)
        c.next() # prime it for iteration
        return c
    return wrapper

class CoroutineProcess(multiprocessing.Process):
    """ Will run a coroutine in its own process, using the
        multiprocessing library. The coroutine thread runs as
        a daemon, and is closed automatically when it is no longer
        needed. Because it exposes send and close methods, a CoroutineProcess
        wrapped coroutine can be dropped in for a regular coroutine."""
    
    def __init__(self, target_func):
        multiprocessing.Process.__init__(self)
        self.in_queue = multiprocessing.Queue() # create a Queue for sending items to the process
        self.processor = target_func
        self.daemon = True
        self.shutdown = multiprocessing.Event() # allows the thread to close correctly

    def send(self, item):
        if self.shutdown.is_set():
            raise StopIteration
        self.in_queue.put(item)
    
    def __call__(self, *args, **kwargs):
        # Prime the wrapped coroutine.
        self.processor = self.processor(*args, **kwargs)
        self.processor.next()
        self.start()
        return self

    def run(self): # this is the isolated 'process' being run after start() is called
        try:
            while True:
                item = self.in_queue.get()
                self.processor.send(item) # throws StopIteration if close() has been called
        except StopIteration:
            pass
        self.close()
    
    def close(self):
        self.processor.close()
        self.shutdown.set()

def coroutine_process(func):
    def wrapper(*args, **kwargs):
        cp = CoroutineProcess(func)
        cp = cp(*args, **kwargs)
        # XXX(todo): use @CoroutineProcess on an individual function, then wrap
        # with @coroutine, too. Don't start until .next().
        return cp
    return wrapper

class CoroutineThread(threading.Thread):
    """ Wrapper for coroutines; runs in their own threads. """
    def __init__(self, target_func):
        threading.Thread.__init__(self) # creates a thread
        self.setDaemon(True)
        self.in_queue = Queue.Queue() # creates a queue for cross-thread communication
        self.processor = target_func # the function to process incoming data
        self.shutdown = threading.Event() # watch for close

    def send(self, item):
        if self.shutdown.isSet():
            raise StopIteration
        self.in_queue.put(item)
    
    def __call__(self, *args, **kwargs):
        # Prime the wrapped coroutine.
        self.processor = self.processor(*args, **kwargs)
        self.processor.next()
        self.start()
        return self
    
    def run(self): # this is running in its own thread after it is created
        try:
            while True:
                item = self.in_queue.get()
                if self.shutdown.is_set(): break
                self.processor.send(item)
        except StopIteration:
            pass
        self.shutdown.set()
    
    def close(self):
        self.shutdown.set()

def coroutine_thread(func):
    def wrapper(*args, **kwargs):
        cp = CoroutineThread(func)
        cp = cp(*args, **kwargs)
        # XXX(todo): use @CoroutineProcess on an individual function, then wrap
        # with @coroutine, too. Don't start until .next().
        return cp
    return wrapper


