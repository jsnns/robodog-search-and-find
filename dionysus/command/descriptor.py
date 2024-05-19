from dataclasses import dataclass
from typing import Callable, Generator
from dionysus.command.base import Command

from dionysus.command.result import CommandResult
from bson import ObjectId


@dataclass
class CommandDescriptor:
    """A descriptor for a command that has been parsed from a chat message."""

    command_name: str
    arguments: dict[str, any]
    run: Callable[[dict[str, any]], Generator[CommandResult, None, None]]
    command: Command
    _id: ObjectId = None

    def __post_init__(self):
        if isinstance(self._id, str):
            self._id = ObjectId(self._id)
        if self._id is None:
            self._id = ObjectId()

    def execute(
        self, *args, **kwargs
    ) -> Generator[CommandResult, None, None]:
        return self.run(self.arguments, *args, **kwargs)

