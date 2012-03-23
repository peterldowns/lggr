# Lggr - easy python logging

Have you ever tried to do anything with the python logging module?

I have. I didn't like it at all. The API was very confusing. Instead of dealing with all of its intricacies, I decided to roll my own.

I've been inspired by [dabeaz](http://www.dabeaz.com/)'s presentation on coroutines and Kenneth Reitz's [presentation](http://python-for-humans.heroku.com/) on better python libraries.

# How does it work?

Create a logger object.

```python
import lggr
d = lggr.Lggr()
```

Add a coroutine (any function or object with `send` and `close` methods) to consume log messages. `lggr` includes some default ones:

* `lggr.Printer()` writes to stdout
* `lggr.StderrPrinter()` writes to stderr
* `lggr.Printer(filepath)` opens a file at `filepath` and writes to that.
* `lggr.SocketWriter(host, port)` writes to a network socket
* `lggr.Emailer(recipients)` sends emails
* `lggr.GMailer(recipients, gmail_username, gmail_password, subject="optional")` also sends emails, but does it from Gmail which is way sexier than doing it from your own server.

You can choose to add different coroutines to different levels of logging. Maybe you want to receive emails for all of your critical messages, but only print to stderr for everything else.

```python
d.add(d.ALL, lggr.Printer()) # d.ALL is a shortcut to add a coroutine to all levels
d.add(d.CRITICAL, lggr.Emailer("peterldowns@gmail.com"))
```

3. Do some logging.

```python
d.info("Hello, world!")
d.warning("Something seems to have gone {desc}", {"desc":"amuck!"})
d.critical("Someone {} us {} the {}!", "set", "up", "bomb")
d.close() # stop logging
```

# What kind of information can I log?
Anything you want. Log messages are created using `str.format`, so you can really create anything you want. The default format includes access to the following variables:

* `levelname` = level of logging as a string (`"INFO"`)
* `levelno` =  level of logging as an integer (`0`)
* `pathname` = path to the file that the logging function was called from (`~/test.py`)
* `filename` = filename the logging function was called from (`test.py`)
* `module` = module the logging function was called from (in this case, `None`)
* `exc_info` = execution information, either passed in or `sys.info()`
* `stack_info` = stack information, created if the `inc_stack_info` argument is `True` or the logging function is called with instance functions `critical`, `debug`, or `error`.
* `lineno` = the line number
* `funcname` = the function name 
* `code` = the exact code that called the logging function
* `codecontext` = surrounding 10 lines surrounding `code`
* `process` = current process id
* `processname` = name of the current process, if `multiprocessing` is available
* `asctime` = time as a string (from `time.asctime()`)
* `time` = time as seconds from epoch (from `time.time()`)
* `threadid` = the thread id, if the `threading` module is available
* `threadname` = the thread name, if the `threading` module is available
* `messagefmt` = the format string to be used to create the log message
* `logmessage` = the user's formatted message
* `defaultfmt` = the default format of a log message

If you want to use any extra information, simply pass in a dict with the named argument `extra`:`

```python
>>> d.config['defaultfmt'] = '{name} sez: {logmessage}'
>>> d.info("This is the {}", "message", extra={"name":"Peter"})
Peter sez: This is the message
```

# What's next?
I'm still working on text-sending and IRC/IM-writing log functions - maybe one of you could help? 

# Who did this?
[Peter Downs.](http://peterdowns.com)  
[peterldowns@gmail.com](mailto:peterldowns@gmail.com)  
[@peterldowns](http://twitter.com/peterldowns)


