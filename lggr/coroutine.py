# coding: utf-8
import sys
import time
import Queue
import threading
import multiprocessing

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

def Coroutine(func):
    """ Decorator for priming co-routines that use (yield) """
    def start(*args, **kwargs):
        c = func(*args, **kwargs)
        c.next() # prime it for iteration
        return c
    return start

@Coroutine
def logger(label):
    """ Prints items with a timestamp. """
    try:
        while True:
            item = (yield)
            timestamp = '(%s) %s:' % (str(label), time.asctime())
            print timestamp, item
    except GeneratorExit: pass

@Coroutine
def counter():
    try:
        count = 0
        while True:
            item = (yield)
            count += 1
            print 'counter: received item #%d' % count
    except GeneratorExit: pass
    
def broadcast(source, coroutines):
    """ Sends data from a source to multiple coroutines """
    # send items to multiple coroutines
    for item in source:
        for c in coroutines:
            c.send(item)

if __name__ == '__main__':
    def start(x):
        x.start()
    def close(x):
        x.close()
    
    print '##### CoroutineProcesses #####'
    processes = map(CoroutineProcess, [logger('process_logger'), counter()])
    map(start, processes) # start the coroutines running in their own processes
    broadcast(xrange(2), processes)
    map(close, processes) # stop the coroutines
    try:
        broadcast([1, 2, 3], processes)
    except StopIteration:
        print '\nThe CoroutineProcesses are now closed and do not accept any more items'
        print '(just like normal coroutines!)'


    print '\n##### CoroutineThreads #####'
    threads = map(CoroutineThread, [logger('thread_logger'), counter()])
    map(start, threads) # start the coroutines in their own threads
    broadcast(xrange(2), threads)
    map(close, threads)
    try:
        broadcast([1, 2, 3], threads)
    except StopIteration:
        print 'The CoroutineThreads are now closed and do not accept any more items'
        print '(just like normal coroutines!)'


    print '\n##### coroutines #####'
    coroutines = [logger('normal_logger'), counter()]
    # don't need to `start` a normal coroutine
    broadcast(xrange(2), coroutines)
    map(close, coroutines)
    try:
        broadcast([1, 2, 3], coroutines)
    except StopIteration:
        print 'After being closed, normal coroutines do not accept any more items'

