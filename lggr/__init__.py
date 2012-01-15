from coroutine import Coroutine
from coroutine import CoroutineProcess
import threading
import traceback
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
ALL = [INFO, WARNING, ERROR, CRITICAL, EXCEPTION]

# ripped from http://hg.python.org/cpython/file/74fa415dc715/Lib/logging/__init__.py#l81
if hasattr(sys, 'frozen'): #support for py2exe
	_srcfile = "logging%s__init%s" % (os.sep, __file[-4:])
else:
	_srcfile = __file__
_srcfile = os.path.normcase(_srcfile)

try:
	import threading
except:
	threading = None
try: 
	import multiprocessing as mp
except:
	mp = None

class Lggr():
	""" Simplified logging. Dispatches messages to any type of
		logging function you want to write, all it has to support
		is send() and close(). """
	def __init__(self, defaultfmt="{asctime} ({levelname}) {logmessage}"):
		self.defaultfmt = defaultfmt
		self.config = {
				EXCEPTION: set(), # these are different levels of logger functions
				CRITICAL: set(),
				ERROR: set(),
				WARNING: set(),
				INFO: set(),
				"defaultfmt": self.defaultfmt # lets lggrname.defaulfmt act as a shortcut
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
		if isinstance(levels, list):
			for lvl in levels:
				self.config[lvl].add(logger)
		else:
			self.config[levels].add(logger)
	
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
	
	def log(self, level, fmt, exc_info=None, stack_info=True, multi_proc=True, *args, **kwargs):
		print level
		""" Send a log message to all of the logging functions
			for a given level as well as adding the
			message to this logger instance's history. """
		if not self.enabled:
			return # Fail silently so that logging can easily be removed
		
		sinfo = None
		if _srcfile:
			#IronPython doesn't track Python frames, so findCaller throws an
			#exception on some versionf of IronPython. We trap it here so that
			#IronPython can use logging.
			try:
				fn, lno, func, sinfo = self.findCaller(stack_info)
			except ValueError:
				fn, lno, func = "(unknown file)", 0, "(unknown function)"
		else:
			fn, lno, func = "(unknown file)", 0, "(unknown function)"

		try:
			fname = os.path.basename(fn)
			module = os.path.splitext(fname)[0]
		except (TypeError, ValueError, AttributeError):
			fname = fn
			module = "Unknown module"

		if exc_info:
			if not isinstance(exc_info, tuple):
				exc_info = sys.exc_info()
		
		log_record = { # This is available information for logging functions.
			#TODO:  proc_name, thread_name
			# see http://hg.python.org/cpython/file/74fa415dc715/Lib/logging/__init__.py#l279
			"args" : args,
			"kwargs" : kwargs,
			"levelname" : level,
			"levelno" : ALL.index(level),
			"pathname" : fn,
			"filename" : fname,
			"module" : module,
			"exc_info" : exc_info,
			"exc_text" : None,
			"stack_info" : sinfo,
			"lineno" : lno,
			"funcname" : func,
			"process" : os.getpid(),
			"processname" : None,
			"asctime": time.asctime(), # TODO: actual specifier for format
			"time" : time.time(),
			"threadid" : None,
			"threadname" : None,
			"messagefmt" : fmt,
			"logmessage" : fmt.format(*args, **kwargs),
			"defaultfmt" : self.config['defaultfmt']
		}
		
		if threading: # check to use threading
			curthread = threading.current_thread()
			log_record.update({
				"threadident" : curthread.ident,
				"threadname" : curthread.name
			})

		if not multi_proc: # check to use multiprocessing
			procname = None
		else:
			procname = "MainProcess"
			if mp:
				try:
					procname = mp.curent_process().name
				except StandardError:
					pass
		log_record.update({
			"procname" : procname
		})



		if 'defaultfmt' in kwargs:
			log_record['defaultfmt'] = kwargs['defaultfmt'] # allow custom formats
		if 'extra' in kwargs:
			log_record.update(kwargs['extra']) # allow custom information to be sent in

		# FINALLY, do the logging
		logstr = log_record['defaultfmt'].format(**log_record) #whoah.
		self.history.append(logstr)
		print "about to do log_funcs=self.config[{}]".format(level)
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
	
	def findCaller(self, stack_info=False):
		"""
		Find the stack frame of the caller so that we can note the source
		file name, line number, and function name
		"""
		f = inspect.currentframe()
		if f is not None:
			f = f.f_back
		rv = ("(unknown file)", 0, "(unknown function)", None)
		while hasattr(f, "f_code"):
			co = f.f_code
			filename = os.path.normcase(co.co_filename)
			if filename == _srcfile:
				f = f.f_back
				continue
			sinfo = None
			if stack_info:
				sinfo = traceback.extract_stack(f)
			rv = (co.co_filename, f.f_lineno, co.co_name, sinfo)
			break
		return rv

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
