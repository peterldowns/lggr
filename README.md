
# Lggr - easy python logging

Have you ever tried to do anything with the python logging module?

I have. I didn't like it at all. The API was very confusing. Instead of dealing with all of its intricacies, I decided to roll my own.

I've been inspired by [dabeaz](http://www.dabeaz.com/)'s presentation on coroutines and Kenneth Reitz's [presentation](http://python-for-humans.heroku.com/) on better python libraries.

# How does it work?

***WARNING: this doc is not up to date. It will be soon. Please refer to the source code.***

Here's an example of adding lggr to an application.

```python
import lggr
logger = lggr.Lggr() # create a logging object
logger.disable() # silently stop logging - for when you don't need it, but might in the future
logger.enable() # turn the logging back on

logger.add(lggr.INFO, lggr.Printerer()) # log all info() calls to STDOUT
logger.add([lggr.CRITICAL], lggr.FilePrinter("output.log")) # log all critical() calls to an output file
logger.add(lggr.ALL, lggr.ErrorPrinter()) # log all logging calls to STDERR

logger.info("Here is a low level warning. It will be written to STDOUT and STDERR")
logger.warning("This is a warning. It is written to STDERR.")
logger.critical("This message will show up on STDERR and also in the \"output.log\" file")

# did I mention that it does arbitrary string.format()ing? yeah.
logger.info("{noun} is so {adjective}, I'd {verb} its {pl_noun}",
			noun="lggr", adjective="cool", verb="test", pl_noun="functions")

logger.warning("WARNING: {} is a {}. You should know this", lggr.Lggr, type(lggr.Lggr))
logger.all("This goes out to every level in {level_list}", level_list=lggr.ALL)

logger.clear(lggr.CRITICAL) # remove all methods from a specific level

logger.close() # stop logging
```

`lggr.Printer`, `lggr.StderrPrinter`, and `lggr.FilePrinter` (as well as `lggr.SocketWriter` and `lggr.Emailer`) are all built-in logging functions that log to STDOUT, STDERR, and a specified file (as well as a host/socket and email addresses), respectively. I think that it really is fine to have the "[Verb]er" name format because, really, that's what they are: these functions return coroutines which do what they say. I.e., `lggr.Printer()` returns a coroutine that writes all items that are `.sent()` to it to `sys.stdout`. 

New logging functions are easy to create because they're coroutines. For example, here's the source for `lggr.SocketWriter`, marked up with extra information.

```python
@Coroutine
def SocketWriter(host, port, af=socket.AF_INET, st=socket.SOCK_STREAM):
	""" Writes messages to a socket/host. """
	# this is the setup area. This is only run once, when the function is called for the first time
	message = "({0}): {1}"
	s = socket.socket(af, st)
	s.connect(host, port)
	try:
		while True:
			item = (yield) # item is an incoming log message. Nothing happens until it is received
			# This is where the message is processed. Here, I send it to a a socket.
			s.send(message.format(time.asctime(), item)) 
	except GeneratorExit:
		# This is where clean-up code should exist. This is run after the coroutine is .close()ed
		s.close()
```

I think that coroutines are a good way of thinking about log functions. After all, they shouldn't do much - just log the message.

# What's next?
I'm still working on emailing, text-sending, and IRC/IM-writing log functions - maybe one of you could help!

# Who did this?
Peter Downs.

peter.l.downs@gmail.com

[@peterldowns](http://twitter.com/peterldowns)

