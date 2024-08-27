import subprocess
from dataclasses import dataclass, field
from functools import cached_property
from typing import Optional
import os


@dataclass
class ResultAdaptor:
    argv: list[str]
    input_file: Optional[str] = None
    output_file: Optional[str] = None
    result: Optional[str] = None
    output_mode: Optional[str] = None

    def invoke(self):
        if self.result is not None:
            return

        input_fd = open(self.input_file) if self.input_file else None
        output_fd = (
            open(self.output_file, self.output_mode if self.output_mode else "w")
            if self.output_file
            else None
        )
        capture_output = self.output_file is None

        res = subprocess.run(
            self.argv, stdin=input_fd, stdout=output_fd, capture_output=capture_output
        )

        if input_fd:
            input_fd.close()

        if output_fd:
            output_fd.flush()
            output_fd.close()

        res.check_returncode()
        if res.stdout:
            self.result = res.stdout.decode()[:-1]

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
