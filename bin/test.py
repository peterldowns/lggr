import lggr
use_gmail = False

d = lggr.Lggr()
d.add(lggr.ALL, lggr.FilePrinter("~/output.log"))
d.add(lggr.ALL, lggr.StderrPrinter())
d.add(lggr.ALL, lggr.Printer())

if use_gmail:
	g_user = raw_input("Gmail address ('user@gmail.com', not 'user'): ")
	g_pass = raw_input("Gmail password: ")
	d.add(lggr.CRITICAL, lggr.GMailer([g_user], g_user, g_pass))

for level in lggr.ALL:
	print "Level {}:".format(level)
	for log_func in d.config[level]:
		print '\t{}'.format(log_func)

d.debug("Hello, ")
d.info("world!")
d.warning("My name is {}", "Peter")
d.error("Testing some {name} logging", {"name":"ERROR"})

old = d.config['defaultfmt']
d.config['defaultfmt'] = '{asctime} ({levelname}) {logmessage}\nIn {pathname}, line {lineno}:\n{codecontext}'
def outer(a):
	def inner(b):
		def final(c):
			d.critical("Easy as {}, {}, {}!", a, b, c)
		return final
	return inner

outer(1)(2)(3)
outer("a")("b")("c")


d.config['defaultfmt'] = old
d.all("This goes out to all of my friends")
d.multi([lggr.WARNING, lggr.INFO], "This is only going to some of my friends")

d.clear(lggr.CRITICAL)
d.clear(lggr.WARNING)
d.clear(lggr.INFO)

d.info("Testing....")
d.error("Testing {} {} {}", "another", "stupid", "thing")

d.shutdown()
d.log(lggr.ALL, "Help?")
