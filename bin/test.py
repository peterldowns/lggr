import lggr
use_gmail = False

mylggr = lggr.Lggr()
mylggr.add(lggr.ALL, lggr.FilePrinter("~/output.log"))
mylggr.add(lggr.ALL, lggr.StderrPrinter())
mylggr.add(lggr.ALL, lggr.Printer())

if use_gmail:
	g_user = raw_input("Gmail address ('user@gmail.com', not 'user'): ")
	g_pass = raw_input("Gmail password: ")
	mylggr.add(lggr.CRITICAL, lggr.GMailer([g_user], g_user, g_pass))

for level in lggr.ALL:
	print "Level {}:".format(level)
	for log_func in mylggr.config[level]:
		print '\t{}'.format(log_func)

mylggr.debug("Hello, ")
mylggr.info("world!")
mylggr.warning("My name is {}", "Peter")
mylggr.error("Testing some {name} logging", {"name":"ERROR"})

old = mylggr.config['defaultfmt']
mylggr.config['defaultfmt'] = '{asctime} ({levelname}) {logmessage}\nIn {pathname}, line {lineno}:\n{codecontext}'
def outer(a):
	def inner(b):
		def final(c):
			mylggr.critical("Easy as {}, {}, {}!", a, b, c)
		return final
	return inner

outer(1)(2)(3)
outer("a")("b")("c")


mylggr.config['defaultfmt'] = old
mylggr.all("This goes out to all of my friends")
mylggr.multi([lggr.WARNING, lggr.INFO], "This is only going to some of my friends")

mylggr.clear(lggr.CRITICAL)
mylggr.clear(lggr.WARNING)
mylggr.clear(lggr.INFO)

mylggr.info("Testing....")
mylggr.error("Testing {} {} {}", "another", "stupid", "thing")

mylggr.shutdown()
mylggr.log(lggr.ALL, "Help?")
