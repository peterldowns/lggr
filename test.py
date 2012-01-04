import lggr

d = lggr.Lggr()

d.add(None, lggr.FilePrinter("output.log"))
d.add(None, lggr.ErrorPrinter())
d.add(None, lggr.Printer())
try:
	d.add(None, lggr.Emailer(["peter.l.downs@gmail.com"], "peter"))
except Exception as e:
	print e

for i, level in enumerate(d.getMethods()):
	print "Level {}:".format(i)
	for item in level:
		print '\t{}'.format(item)

d.info("Hello, world!")
d.warning("My name is {}", "Peter")
d.error("Testing some {name} logging", name="ERROR")
d.critical("Oh shit, nigel. Something is horribly wrong.")

d.clear(lggr.CRITICAL)
d.clear(lggr.WARNING)
d.clear(lggr.INFO)

d.info("Testing....")
d.error("Testing {0} {1} {2}", "another", "stupid", "thing")

d.close()
