import logging
from typing import List
from dionysus.argument.base import Argument
from dionysus.argument_type.primative import String
from dionysus.command.base import Command
from dionysus.commandset import CommandSet


class MoveRobot(Command):
    arguments: List[Argument] = [
        Argument("direction", String(), choices=["forward", "backward"]),
        Argument("reason", String())
    ]

    def run(self, command_args, *args, **kwargs):
        logging.info(f"Moving robot {command_args['direction']}. Reason={command_args['reason']}")


class RotateRobot(Command):
    arguments: List[Argument] = [
        Argument("direction", String(), choices=["clockwise", "counter-clockwise"]),
        Argument("reason", String())
    ]

    def run(self, command_args, *args, **kwargs):
        logging.info(f"Rotating robot {command_args['direction']}. Reason={command_args['reason']}")


movement_commands = CommandSet.from_definitions([MoveRobot, RotateRobot])