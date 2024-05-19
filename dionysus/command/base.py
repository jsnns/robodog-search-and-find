from time import perf_counter
from typing import Generator

from dionysus.argument_type.compound_argument import CompoundArgument
from dionysus.command.result import CommandResult
from dionysus.command.thought_chain import Step


class Command(CompoundArgument):
    parent = "command"
    action_name_for_end_user = "Command"
    START = "{"
    END = "}"

    @classmethod
    def user_thought_chain_explaination(cls) -> Step:
        return Step.do(cls.action_name_for_end_user)

    def handle_visitor(self, args, context):
        from dionysus.command.descriptor import CommandDescriptor

        if isinstance(args, list):
            args = {}

        return CommandDescriptor(
            command_name=self.name,
            arguments=args,
            command=self,
            run=self.execute,
        )

    def execute(self, command_args, *args, **kwargs) -> Generator[CommandResult, None, None]:
        """Execute the command and lifecycle methods to create a list of results."""
        self.pre_run(command_args, *args, **kwargs)
        for result in self.run(command_args, *args, **kwargs) or []:
            yield result
        self.post_run(command_args, *args, **kwargs)

    def pre_run(self, command_args, *args, **kwargs):
        pass

    def run(self, command_args, *args, **kwargs) -> Generator[CommandResult, None, None]:
        """Run the command and return a list of results."""
        raise NotImplementedError

    def post_run(self, command_args, *args, **kwargs):
        pass

    def external_explaination(self) -> str:
        return self.action_name_for_end_user
