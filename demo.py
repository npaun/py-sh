from sh import sh

print(sh.date())
print(sh.git.ls_files())
print(sh.git.log(S="import"))
