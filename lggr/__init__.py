from coroutine import Coroutine
import inspect
import smtplib
import socket
import types
import time
import sys

EXCEPTION = "EXCEPTION"
CRITICAL = "CRITICAL"
ERROR = "ERROR"
WARNING = "WARNING"
INFO = "INFO"
ALL = [EXCEPTION, CRITICAL, ERROR, WARNING, INFO]

class Lggr():
	""" Simplified logging. Dispatches messages to any type of
		logging function you want to write, all it has to support
		is send() and close(). """
	def __init__(self):
		self.config = {
				EXCEPTION: set(),
				CRITICAL: set(),
				ERROR: set(),
				WARNING: set(),
				INFO: set()
			}
		self.history = []
		self.enabled = True
	
	def disable(self):
		""" Turn off logging. """
		self.enabled = False
	
	def enable(self):
		""" Turn on logging. Enabled by default. """
		self.enabled = True
	
	def close(self):
		for level in ALL:
			self.clear(level)
	
	def add(self, levels, logger):
		""" Given a list of logging levels, add a logger
			instance to each. """
		for lvl in levels:
			self.config[lvl].add(logger)
	
	def remove(self, level, logger):
		""" Given a level, remove a given logger function
			if it is a member of that level, closing the logger
			function either way."""
		self.config[level].discard(logger)
		logger.close()
	
	def clear(self, level):
		""" Remove all logger functions from a given level. """
		for item in self.config[level]:
			item.close()
		self.config[level].clear()
	
	def log(self, levels, fmt, *args, **kwargs):
		""" Send a log message to all of the logging functions
			for each level in a given list, as well as adding the
			message to this logger instance's history. """
		if not self.enabled:
			return # Fail silently so that logging can easily be removed

		message = fmt.format(*args, **kwargs) 

		for lvl_name in levels:
			self.history.append((time.time(), lvl_name, message))
			log_funcs = self.config[lvl_name]
			for lf in log_funcs.copy(): # so that we can edit the original while iterating
				try:
					lf.send(message)
				except StopIteration: # already closed
					self.remove(lvl_name, lf)
					self.info("Logging function {} in level {} stopped.", lf, lvl_name)

	def critical(self, msg, *args, **kwargs):
		""" Log a message with CRITICAL level """
		self.log([CRITICAL], msg, *args, **kwargs)

	def error(self, msg, *args, **kwargs):
		""" Log a message with ERROR level """
		self.log([ERROR], msg, *args, **kwargs)

	def warning(self, msg, *args, **kwargs):
		""" Log a message with WARNING level """
		self.log([WARNING], msg, *args, **kwargs)
		
	def info(self, msg, *args, **kwargs):
		""" Log a message with INFO level """
		self.log([INFO], msg, *args, **kwargs)
	def all(self, msg, *args, **kwargs):
		""" Log a message at all levels """
		self.log(ALL, msg, *args, **kwargs)

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

def StderrPrinter():
	""" Prints items to stderr. """
	return Printer(open_file=sys.stderr, closing=False)

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
	""" Sends messages as emails to the given list
		of recipients. """
	hostname = socket.gethostname()
	if not sender:
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
