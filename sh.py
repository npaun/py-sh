import subprocess
from dataclasses import dataclass, field
from functools import cached_property
from typing import Optional
from pathlib import Path
import os


@dataclass
class ResultAdaptor:
    argv: list[str]
    input_file: Optional[str] = None
    output_file: Optional[str] = None
    result: Optional[str] = None
    output_mode: Optional[str] = None

    @staticmethod
    def get_fd(value, mode):
        if value is None:
            return None

        if isinstance(value, (str, Path)):
            return open(value, mode)
    
        return value
    
    def exec(self, input_fd, output_fd):
        return subprocess.Popen(self.argv, stdin=input_fd, stdout=output_fd)

    def invoke(self):
        if self.result is not None:
            return

        input_fd = ResultAdaptor.get_fd(self.input_file, 'r')
        output_fd =  ResultAdaptor.get_fd(self.output_file, self.output_mode or 'w') or subprocess.PIPE

        proc = self.exec(input_fd, output_fd)
        (stdout, stderr) = proc.communicate()
        
        if input_fd:
            input_fd.close()

        if output_fd is not subprocess.PIPE:
            output_fd.flush()
            output_fd.close()

        if proc.returncode != 0:
            raise ValueError('oh man')

        if stdout:
            self.result = stdout.decode()[:-1]

    def run(self):
        self.invoke()
        return self.result

    def __str__(self):
        self.invoke()
        return self.result

    def __repr__(self):
        self.invoke()
        return repr(self.result)

    def __iter__(self):
        self.invoke()
        return iter(self.result.splitlines())

    def __lt__(self, input_file):
        return ResultAdaptor(
            self.argv, input_file=input_file, output_file=self.output_file
        )

    def __gt__(self, output_file):
        return ResultAdaptor(
            self.argv, input_file=self.input_file, output_file=output_file
        )

    def __rshift__(self, output_file):
        return ResultAdaptor(
            self.argv,
            input_file=self.input_file,
            output_file=output_file,
            output_mode="a",
        )

    def __or__(self, next_command):
        return PipelineAdaptor([self, next_command])

@dataclass
class PipelineAdaptor:
    commands: list[ResultAdaptor]

    def __or__(self, next_command):
        return PipelineAdaptor([*self.commands, next_command])

    def run(self):
        for command in self.commands:
            print(command.argv)
            proc = command.exec(stdin, subprocess.PIPE)
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
