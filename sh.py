import subprocess
from dataclasses import dataclass, field
from functools import cached_property
from typing import Optional, Any
from pathlib import Path
import os

@dataclass
class FDSetter:
    thiz: Any
    fd: Optional[int] = None

    def _assign_fd(self, obj, default_fd, mode):
        fd = self.fd if self.fd is not None else default_fd
        if hasattr(obj, 'read'):
            self.thiz.fds[fd] = obj
        else:
            self.thiz.fds[fd] = open(obj, mode)

    def __gt__(self, sink):
        self._assign_fd(sink, 1, 'w')
        return self.thiz

    def __rshift__(self, sink):
        self._assign_fd(sink, 1, 'a')
        return self.thiz

    def __lt__(self, source):
        self._assign_fd(source, 0, 'r')
        return self.thiz



@dataclass
class ResultAdaptor:
    argv: list[str]
    result: Optional[str] = None
    fds: dict[int, Any] = field(default_factory=dict)
    require_success: bool = True

    def exec(self, fds):
        return subprocess.Popen(self.argv, stdin=fds.get(0), stdout=fds.get(1, subprocess.PIPE), stderr=fds.get(2))

    def invoke(self):
        if self.result is not None:
            return

        print(self.fds)
        proc = self.exec(self.fds)
        (stdout, stderr) = proc.communicate()
       
        for fd in self.fds.values():
            fd.close()

        if self.require_success and proc.returncode != 0:
            raise ValueError('oh man')

        if stdout:
            self.result = stdout
        else:
            self.result = b''

    def run(self):
        self.invoke()
        return self.result

    def __str__(self):
        self.invoke()
        return self.result.decode()[:-1]

    def __repr__(self):
        self.invoke()
        return repr(self.result.decode()[:-1])

    def __iter__(self):
        self.invoke()
        return iter(self.result.decode()[:-1].splitlines())

    def __bytes__(self):
        self.invoke()
        return self.result

    def __int__(self):
        return int(str(self))

    def __bool__(self):
        return bool(int(self))

    def __float__(self):
        return float(str(self))

    def __contains__(self, query):
        return query in str(self)

    def __eq__(self, other):
        return str(self) == other

    def __lt__(self, input_file):
        return FDSetter(self, None) < input_file

    def __gt__(self, output_file):
        return FDSetter(self, None) > output_file

    def __rshift__(self, output_file):
        return FDSetter(self, None) >> output_file

    def output_to(self, output_file):
        FDSetter(self, 1) > output_file
        FDSetter(self, 2) > output_file
        return self

    def fd(self, fileno):
        return FDSetter(self, fileno)

    def or_true(self):
        self.require_success = False
        return self

    def __or__(self, next_command):
        return PipelineAdaptor([self, next_command])

@dataclass
class PipelineAdaptor:
    commands: list[ResultAdaptor]

    def __or__(self, next_command):
        return PipelineAdaptor([*self.commands, next_command])

    def run(self):
        stdin = None
        for command in self.commands:
            proc = command.exec({0: stdin, 1: subprocess.PIPE})
            stdin = proc.stdout
           
        # We have the last proc, now drain it
        stdout, stderr = proc.communicate()

        if stdout is not None:
            return stdout.decode()[:-1]
 

@dataclass
class CommandAdaptor:
    prefix: list[str] = field(default_factory=list)

    def __call__(self, *args, **kwargs):
        argv = [*self.prefix]
        for key, value in kwargs.items():
            if len(key) == 1:
                option = f"-{key}"
            else:
                # FIXME: a lot of dodgy tools use a single - for long options too
                # FIXME: a lot of dodgy tools use underscores in long option names
                key_norm = key.replace("_", "-")
                option = f"--{key_norm}"

            if value == True:
                # Acting like a flag
                argv.extend([option])
            else:
                # Actual operand
                argv.extend([option, str(value)])

        argv.extend(args)
        return ResultAdaptor(argv)

    def __getattr__(self, arg):
        # FIXME might need to run a tool with an underscore in its name
        return CommandAdaptor([*self.prefix, arg.replace("_", "-")])


sh = CommandAdaptor()
