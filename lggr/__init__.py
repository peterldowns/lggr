from coroutine import Coroutine
from coroutine import CoroutineProcess
from coroutine import CoroutineThread
import traceback
import inspect
import time
import sys
import os

DEBUG = "DEBUG"
INFO = "INFO"
WARNING = "WARNING"
ERROR = "ERROR"
CRITICAL = "CRITICAL"
ALL = [DEBUG, INFO, WARNING, ERROR, CRITICAL] # shortcut

# Allow function, module, sourcecode information
# ripped from http://hg.python.org/cpython/file/74fa415dc715/Lib/logging/__init__.py#l81
if hasattr(sys, 'frozen'): #support for py2exe
	_srcfile = "logging%s__init%s" % (os.sep, __file[-4:])
else:
	_srcfile = __file__
_srcfile = os.path.normcase(_srcfile)

# 
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
				CRITICAL: set(), # these are different levels of logger functions
				ERROR: set(),
				DEBUG: set(),
				WARNING: set(),
				INFO: set(),
				"defaultfmt": self.defaultfmt # lets lggrname.defaulfmt act as a shortcut
			}
		self.history = []
		self.enabled = True
		self.ALL = ALL # allow instance.ALL instead of just lggr.ALL
	

	def disable(self):
		""" Turn off logging. """
		self.enabled = False
	
	def enable(self):
		""" Turn on logging. Enabled by default. """
		self.enabled = True
	
	def close(self):
		""" Stop and remove all logging functions
			and disable this logger. """
		for level in ALL:
			self.clear(level)
		self.disable()
	
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
	
	def makeRecord(self, level, fmt, args, extra, exc_info, inc_stack_info, inc_multi_proc):
		""" Create a 'record' (a dictionary) with information to be logged. """
		
		args_dict=False
		if args and len(args) == 1 and isinstance(args[0], dict) and args[0]:
			# args can be a list of unnamed variables or a dict of named variables
			# to be used with str.format()
			args = args[0]
			args_dict=True
		
		sinfo = None
		if _srcfile:
			#IronPython doesn't track Python frames, so findCaller throws an
			#exception on some versionf of IronPython. We trap it here so that
			#IronPython can use logging.
			try:
				fn, lno, func, code, cc, sinfo = self.findCaller(inc_stack_info)
			except ValueError:
				fn, lno, func, code, cc, sinfo = "(unknown file)", 0, "(unknown function)", "(code not available)", [], None
		else:
			fn, lno, func, code, cc, sinfo = "(unknown file)", 0, "(unknown function)", "(code not available)", [], None
		try:
			fname = os.path.basename(fn)
			module = os.path.splitext(fname)[0]
		except (TypeError, ValueError, AttributeError):
			fname = fn
			module = "Unknown module"

		if not exc_info or not isinstance(exc_info, tuple):
			# Allow passed in exc_info, but supply it if it isn't
			exc_info = sys.exc_info()
		
		log_record = { # This is available information for logging functions.
			#TODO:  proc_name, thread_name
			# see http://hg.python.org/cpython/file/74fa415dc715/Lib/logging/__init__.py#l279
			"args" : args,
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
			"code": code,
			"codecontext": "".join(cc),
			"process" : os.getpid(),
			"processname" : None,
			"asctime": time.asctime(), # TODO: actual specifier for format
			"time" : time.time(),
			"threadid" : None,
			"threadname" : None,
			"messagefmt" : fmt,
			"logmessage" : None,
			# The custom `extra` information can only be used to format the default
			#   format. The `logmessage` can only be passed a dictionary or a list
			#   (as `args`).
			"defaultfmt" : self.config['defaultfmt']
		}
		# If the user passed a single dict, use that with format.
		# Otherwise, format using the passed args
		if args_dict:
			log_record['logmessage'] = fmt.format(**args)
		else:
			log_record['logmessage'] = fmt.format(*args)

		if extra:
			log_record.update(extra) # add custom variables to record
		
		if threading: # check to use threading
			curthread = threading.current_thread()
			log_record.update({
				"threadid" : curthread.ident,
				"threadname" : curthread.name
			})

		if not inc_multi_proc: # check to use multiprocessing
			procname = None
		else:
			procname = "MainProcess"
			if mp:
				try:
					procname = mp.curent_process().name
				except StandardError:
					pass
		log_record.update({
			"processname" : procname
		})

		return log_record

	def log(self, level, fmt, args=None, extra=None, exc_info=None, inc_stack_info=False, inc_multi_proc=False):
		""" Send a log message to all of the logging functions
			for a given level as well as adding the
			message to this logger instance's history. """
		if not self.enabled:
			return # Fail silently so that logging can easily be removed

		log_record = self.makeRecord(level, fmt, args, extra, exc_info, inc_stack_info, inc_multi_proc)

		logstr = log_record['defaultfmt'].format(**log_record) #whoah.
		
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
			self.info("Logging function {} removed from level {}", lf, level)

#debug, info, warning, error, critical
	def info(self, msg, *args, **kwargs):
		"""" Log a message with INFO level """   
		self.log(INFO, msg, args, **kwargs)
	
	def warning(self, msg, *args, **kwargs):
		""" Log a message with WARNING level """
		self.log(WARNING, msg, args, **kwargs)

	def debug(self, msg, *args, **kwargs):
		""" Log a message with DEBUG level. Automatically
			includes stack info unless it is specifically not
			included. """
		kwargs["inc_stack_info"] = kwargs.get("inc_stack_info", True)
		self.log(DEBUG, msg, args, **kwargs)
	
	def error(self, msg, *args, **kwargs):
		""" Log a message with ERROR level. Automatically
			includes stack and process info unless they
			are specifically not included. """
		kwargs["inc_stack_info"] = kwargs.get("inc_stack_info", True)
		kwargs["inc_multi_proc"] = kwargs.get("inc_multi_proc", True)
		self.log(ERROR, msg, args, **kwargs)

	def critical(self, msg, *args, **kwargs):
		""" Log a message with CRITICAL level. Automatically
			includes stack and process info unless they are
			specifically not included. """
		kwargs["inc_stack_info"] = kwargs.get("inc_stack_info", True)
		kwargs["inc_multi_proc"] = kwargs.get("inc_multi_proc", True)
		self.log(CRITICAL, msg, args, **kwargs)
		
	def multi(self, lvl_list, msg, *args, **kwargs):
		""" Log a message at multiple levels"""
		for level in lvl_list:
			self.log(level, msg, args, **kwargs)

	def all(self, msg, *args, **kwargs):
		""" Log a message at every known log level """
		self.multi(ALL, msg, args, **kwargs)
	
	def findCaller(self, stack_info=False):
		"""
		Find the stack frame of the caller so that we can note the source
		file name, line number, and function name
		"""
		f = inspect.currentframe()
		rv = ("(unknown file)", 0, "(unknown function)", "(code not available)", [], None)
		while hasattr(f, "f_code"):
			co = f.f_code
			filename = os.path.normcase(co.co_filename)
			if filename == _srcfile:
				f = f.f_back # get out of this logging file
				continue
			sinfo = None
			if stack_info:
				sinfo = traceback.extract_stack(f)
				fname, lno, fnc, cc, i = inspect.getframeinfo(f, context=10)
				cc[i] = ">" + cc[i] # mark the exact line
				code = cc[i]
				rv = (fname, lno, fnc, code, cc, sinfo)
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
	path = os.path.abspath(os.path.expanduser(filename))
	""" Opens the given file and returns a printer to it. """
	f = open(path, mode)
	return Printer(f, closing)

import socket
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

import smtplib
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
