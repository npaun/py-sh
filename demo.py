from sh import sh

print(repr(sh.date()))
print(list(sh.git.ls_files()))
print(sh.git.log(S="import"))
print(sh.sort() < "/etc/passwd")
(sh.uptime() >> "uptime.txt").run()
