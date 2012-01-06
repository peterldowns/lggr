import lggr

d = lggr.Lggr()

d.add(lggr.ALL, lggr.FilePrinter("output.log"))
d.add(lggr.ALL, lggr.StderrPrinter())
d.add(lggr.ALL, lggr.Printer())
try:
	d.add(lggr.ALL, lggr.Emailer(["peter.l.downs@gmail.com"], "peter"))
except Exception as e:
	print e

for level in lggr.ALL:
	print "Level {}:".format(level)
	for log_func in d.config[level]:
		print '\t{}'.format(log_func)

d.info("Hello, world!")
d.warning("My name is {}", "Peter")
d.error("Testing some {name} logging", name="ERROR")
d.critical("Oh shit, nigel. Something is horribly wrong.")
d.all("This goes out to all of my friends")
d.multi([lggr.WARNING, lggr.INFO], "This is only going to some of my friends")

d.clear(lggr.CRITICAL)
d.clear(lggr.WARNING)
d.clear(lggr.INFO)

d.info("Testing....")
d.error("Testing {0} {1} {2}", "another", "stupid", "thing")
d.info("Here's something new. I changed the default {}!", "format",
		default_fmt="[{descriptor} @ {asctime}] {log_message}",
		extra={"descriptor":"custom-log-message"})

d.close()
