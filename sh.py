import subprocess
from dataclasses import dataclass, field



@dataclass
class CommandAdaptor:
    prefix: list[str] = field(default_factory=list)

    def __call__(self, *args, **kwargs):
        argv = [*self.prefix]
        for key, value in kwargs.items():
            if len(key) == 1:
                option = f'-{key}'
            else:
                # FIXME: a lot of dodgy tools use a single - for long options too 
                # FIXME: a lot of dodgy tools use underscores in long option names
                key_norm = key.replace('_','-')
                option = f'--{key_norm}'
            
            if value == True:
                # Acting like a flag
                argv.extend([option])
            else:
                # Actual operand
                argv.extend([option, str(value)])

        argv.extend(args)
        res = subprocess.run(argv, capture_output=True)
        res.check_returncode()
        return res.stdout.decode()[:-1]

    def __getattr__(self, arg):
        # FIXME might need to run a tool with an underscore in its name
        return CommandAdaptor([*self.prefix, arg.replace('_','-')])


sh = CommandAdaptor()
