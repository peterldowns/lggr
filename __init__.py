from coroutine import Coroutine
import smtplib
import socket
import types
import time
import sys

CRITICAL = 0
ERROR = 1
WARNING = 2
INFO = 3

class Lggr():
	""" Simplified logging. Dispatches messages to any type of
		logging function you want to write, all it has to support
		is send() and close(). """
	CRITICAL = 0
	ERROR = 1
	WARNING = 2
	INFO = 3
	def __init__(self):
		self.loggers = [set() for i in xrange(4)]
		self.history = []
		self.turned_on = True
	
	def disable(self):
		""" Turn off logging. """
		self.turned_on = False
	
	def enable(self):
		""" Turn on logging. Enabled by default. """
		self.turned_on = True
	
	def close(self):
		self.clearMethods()

	
	def addMethod(self, level, logger):
		""" Add a logging function to a specified level of importance.
			If the level is None, then add the logging function to ALL
			levels. """
		if level is None:
			for level in self.loggers:
				level.add(logger)
		else:
			self.loggers[level].add(logger)
	
	def removeMethod(self, level, logger):
		""" If a logging function exists at a level,
			remove it. If level is None, then remove the
			logging function from all levels on which it exists. """
		def delMeth(lvl, logger):
			try:
				item = lvl.pop(logger)
				item.close()
			except KeyError: pass
		
		if level is None:
			for lvl in self.loggers:
				delMeth(lvl, logger)
		else:
			delMeth(self.loggers[level], logger)
	
	def getMethods(self, level=None):
		""" Return a list of the logger functions associated with
			a logging level. If the level is none, return a list 
			of lists of these functions for each level, in order. """
		if level == None:
			return map(list, self.loggers)
		return list(self.loggers[level])

	def clearMethods(self, level=None):
		""" Remove all logger functions from a given level. If the
			level is none, remove all logger functions. """
		def clrMeth(lvl):
			for item in lvl:
				item.close()
			lvl.clear()
		
		if level:
			clrMeth(self.loggers[level])
		else:
			for lvl in self.loggers:
				clrMeth(lvl)
	
	def logHistory(self):
		""" Return the internal history of all calls to log(). """
		return self.history
	
	def log(self, level, fmt, *args, **kwargs):
		""" Send a log message to all of the activated logging
			functions and add it to the instance's history. """
		message = fmt.format(*args, **kwargs) 
		self.history.append((time.time(), level, message))
	
		if not self.turned_on:
			print "I AM NOT TURNED ON"
			return # Fail silently so that logging can easily be removed

		levset = self.loggers[level]
		for logger in levset:
			try:
				logger.send(message)
			except StopIteration: # already closed
				self.removeMethod(levset, logger)
				self.info("Logging function {} in level {} stopped.", logger, levset)

	def critical(self, msg, *args, **kwargs):
		""" Log a message with CRITICAL level """
		self.log(CRITICAL, msg, *args, **kwargs)

	def error(self, msg, *args, **kwargs):
		""" Log a message with ERROR level """
		self.log(ERROR, msg, *args, **kwargs)

	def warning(self, msg, *args, **kwargs):
		""" Log a message with WARNING level """
		self.log(WARNING, msg, *args, **kwargs)
		
	def info(self, msg, *args, **kwargs):
		""" Log a message with INFO level """
		self.log(INFO, msg, *args, **kwargs)

@Coroutine
def Printer(open_file=sys.stdout, closing=False):
	""" Prints items with a timestamp. """
	message = "({0}): {1}\n"
	try:
		while True:
			item = (yield)
			open_file.write(message.format(time.asctime(), item))
	except GeneratorExit:
		if closing:
			try: open_file.close()
			except: pass

@Coroutine
def ErrorPrinter():
	""" Prints items to stderr. """
	return Printer(open_file=sys.stderr, closing=False)

@Coroutine
def FilePrinter(filename, mode='a', closing=True):
	""" Opens the given file and returns a printer to it. """
	f = open(filename, mode)
	return Printer(f, closing)

@Coroutine
def SocketWriter(host, port, af=socket.AF_INET, st=socket.SOCK_STREAM):
	""" Writes messages to a socket/host. """
	message = "({0}): {1}"
	s = socket.socket(af, st)
	s.connect(host, port)
	try:
		while True:
			item = (yield)
			s.send(message.format(time.asctime(), item))
	except GeneratorExit:
		s.close()

@Coroutine
def Emailer(recipients, sender=None):
	""" Sends messages as emails. """
	if type(recipients) is not types.ListType:
		recipients = [recipients]
	hostname = socket.gethostname()
	sender = "lggr@{}".format(hostname)
	smtp = smtplib.SMTP('localhost')
	try:
		while True:
			item = (yield)
			try:
				smtp.sendmail(sender, recipients, item)
			except smtplib.SMTPExcpetion:
				pass
	except GeneratorExit:
		smtp.quit()
