from coroutine import Coroutine
from coroutine import CoroutineProcess
import threading
import inspect
import smtplib
import socket
import time
import sys
import os

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
	def __init__(self, default_fmt="{asctime} ({level}) {log_message}"):
		self.config = {
				EXCEPTION: set(), # these are different levels of logger functions
				CRITICAL: set(),
				ERROR: set(),
				WARNING: set(),
				INFO: set(),
				"default_fmt": default_fmt
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
	
	def log(self, level, fmt, *args, **kwargs):
		""" Send a log message to all of the logging functions
			for a given level as well as adding the
			message to this logger instance's history. """
		if not self.enabled:
			return # Fail silently so that logging can easily be removed

		log_record = { # This is available information for logging functions.
			#TODO:  proc_name, thread_name, filename, funcname, lineno, module, pathname
			"args" : args,
			"kwargs" : kwargs,
			"asctime": time.asctime(), # TODO: actual specifier
			"time" : time.time(),
			"exc_info" : sys.exc_info(),
			"level" : level,
			"message_fmt" : fmt,
			"log_message" : fmt.format(*args, **kwargs),
			"proc_id" : os.getpid(),
			"thread" : threading.currentThread(),
			"default_fmt" : self.config['default_fmt'],
		}

		if 'default_fmt' in kwargs:
			log_record['default_fmt'] = kwargs['default_fmt'] # allow custom formats
		if 'extra' in kwargs:
			log_record.update(kwargs['extra']) # allow custom information to be sent in

		logstr = log_record['default_fmt'].format(**log_record) #whoah.

		self.history.append(logstr)

		log_funcs = self.config[level]
		to_remove = []
		for lf in log_funcs:
			try:
				lf.send(logstr)
			except StopIteration: # already closed, add it to the list to be deleted
				to_remove.append(lf)
		for lf in to_remove:
			self.remove(level, lf)
			self.info("Logging function {} in level {} stopped.", lf, level)

	def exception(self, msg, *args, **kwargs):
		""" Log a message with EXCEPTION level """
		self.log(EXCEPTION, msg, *args, **kwargs)

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
		
	def multi(self, lvl_list, msg, *args, **kwargs):
		""" Log a message at multiple levels"""
		for level in lvl_list:
			self.log(level, msg, *args, **kwargs)

	def all(self, msg, *args, **kwargs):
		""" Log a message at every known log level """
		self.multi(ALL, msg, *args, **kwargs)

@Coroutine
def Printer(open_file=sys.stdout, closing=False):
	""" Prints items with a timestamp. """
	try:
		while True:
			logstr = (yield)
			open_file.write(logstr)
			open_file.write('\n') # new line
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
			logstr = (yield)
			s.send(logstr)
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
			logstr = (yield)
			try:
				smtp.sendmail(sender, recipients, logstr)
			except smtplib.SMTPExcpetion:
				pass
	except GeneratorExit:
		smtp.quit()
