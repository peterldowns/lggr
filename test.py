import lggr

d = lggr.Lggr()

d.add(lggr.ALL, lggr.PrintToFile("output.log"))
d.add(lggr.ALL, lggr.PrintError())
d.add(lggr.ALL, lggr.Print())
try:
	d.add(None, lggr.SendEmail(["peter.l.downs@gmail.com"], "peter"))
except Exception as e:
	print e

for level, log_funcs in d.config.iteritems():
	print "Level {}:".format(level)
	for lf in log_funcs:
		print '\t{}'.format(lf)

d.info("Hello, world!")
d.warning("My name is {}", "Peter")
d.error("Testing some {name} logging", name="ERROR")
d.critical("Oh shit, nigel. Something is horribly wrong.")
d.all("This goes out to all of my friends")

d.clear(lggr.CRITICAL)
d.clear(lggr.WARNING)
d.clear(lggr.INFO)

d.info("Testing....")
d.error("Testing {0} {1} {2}", "another", "stupid", "thing")

d.close()
