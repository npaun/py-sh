# py-sh

An easy way to write shell scripts in Python. Abuses operator overloading to provide convenient shell-like syntax. 

## Reference

### Importing `sh`
`from sh import sh`

### Supported syntax

| Shell syntax                            | Python "syntax"                                             | Description                                                |
|-----------------------------------------|-------------------------------------------------------------|------------------------------------------------------------|
| `date`                                  | `sh.date()`                                                 | Specify the command to run                                 |
| `git log`                               | `sh.git.log()`                                              | `.` can be chained to add subcommands before args begin    |
| `git log -S password`                   | `sh.git.log(S='password')`                                  | Single letter kwargs become short options                  |
| `git commit --message 'initial commit'` | `sh.git.commit(message='initial commit')`                   | Other kwargs become long options                           |
| `git diff --name-only`                  | `sh.git.diff(name_only=True)`                               | Setting a kwarg to True acts like a flag (no argument)     |
| `rsync config.json server:/etc/`        | `sh.rsync('config.json', 'server:/etc/')`                   | Positional args in Python become positional command args   |
| `uptime > uptime.txt`                   | `sh.uptime() > 'uptime.txt'`                                | `>` implements redirection to a filename                   |
| `uptime >> uptimes.txt`                 | `sh.uptime() >> 'uptimes.txt'`                              | `>>` implements append to a filename                       |
| `sort < index.txt`                      | `sh.sort() < 'index.txt'`                                 | `>` implements redirection from a filename                 |
| &mdash;                                 | `sh.uptime() > open('uptime.txt')`                          | The operand may also be a native Python file object        |
| <code>git shortlog \| sort -r \| gzip log.txt</code> | <code>sh.git.shortlog() \| sh.sort(r=True)  \| sh.gzip('log.txt')</code> | <code>\|</code> implements a pipeline between processes                |


### Lazy loading

The output of commands is lazily loaded. Commands are only run once you interact with the result in some way.
 
| Python "syntax"                     | Description                                                   |
|-------------------------------------|---------------------------------------------------------------|
| `sh.reboot().run()`                 | Force evaluation                                              |
| `str(sh.date())`                    | Cast to string                                                |
| `repr(sh.date())`                   | Repr builtin                                                  |
| `list(sh.git.diff(name_only=True))` | Any kind of iteration will split on newlines                  |
| `print(sh.date())`                  | Note: printing works automatically because of the rules above |

