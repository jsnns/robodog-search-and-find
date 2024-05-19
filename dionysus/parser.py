import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Tuple, Type

from lark import Lark, ParseTree, Transformer, exceptions

from dionysus.argument_type.base import ArgumentType
from dionysus.argument_type.groups import Group
from dionysus.command.base import Command
from dionysus.command.descriptor import CommandDescriptor
from dionysus.commandset import CommandSet

BASE_LARK = """%import common.WS
%import common.ESCAPED_STRING
%import common.WORD
%import common.CNAME
%ignore WS
argument_name: CNAME -> argument_name
estring: ESCAPED_STRING
bool: /true|false/
"""


@dataclass
class ChatResultParser:
    commandset: CommandSet
    current_message: str = None

    def base_lark(self) -> str:
        """Build the base lark grammar for this command set"""
        return f"{BASE_LARK.strip()}\n"

    def build_lark_grammar(self) -> str:
        """Build the entire lark grammar for this command set"""
        lark = self.base_lark()
        for type in self.commandset.type_dependencies():
            lark += type().full_lark + "\n"

        command_names = " | ".join([command.lark_name for command in self.commandset.commands])
        lark += f"start: ({command_names})+\n"

        lark += "ignore: /[^}]+/"

        return lark

    def as_parser(self):
        """Build the entire lark parser for this command set"""
        return Lark(self.build_lark_grammar(), start="start")

    def as_transformer(self):
        """Build the entire lark transformer for this command set"""
        transformer = Transformer()
        setattr(transformer, "pluto_context", {})

        for type in self.commandset.type_dependencies():
            dr = type().visitor_delegate

            def delegate(args, dr=dr):
                return dr(args, transformer)

            setattr(transformer, type().lark_name, delegate)

        setattr(transformer, "list", lambda args: args or [])
        setattr(transformer, "argument_name", lambda args: args[0])
        setattr(transformer, "argument", lambda args: (args[0], args[1]))
        setattr(transformer, "start", lambda args: args)
        setattr(transformer, "word", lambda args: args[0])
        setattr(transformer, "estring", lambda args: args[0][1:-1])

        def on_ignore(args):
            logging.error(
                f"ignoring text from parsed message {[str(a) for a in args] if isinstance(args, list) else args}"
            )

        setattr(transformer, "ignore", on_ignore)

        return transformer

    def parse(self, string):
        """Parse a string into a command"""
        string = self.extract_commands_from_message(string)

        if not string:
            return []

        try:
            tree = self.as_parser().parse(string)
        except exceptions.UnexpectedCharacters as e:
            # adding the original message to the exception for better visibility later
            e.full_seq = string
            raise e

        return tree

    def transform(self, tree: ParseTree):
        """Transform a parse tree into a command"""
        return self.as_transformer().transform(tree)

    def __call__(self, string) -> List[CommandDescriptor]:
        """Parse and transform a string into a command"""
        split_commands = self.split_commands_for_seperate_parsing(string)
        results = []

        for command in split_commands:
            try:
                self.current_message = string
                tree = self.parse(command)
                if not tree:
                    return []
                results.extend(self.transform(tree))
            except Exception as e:
                logging.exception(e)
                logging.error(
                    f"Failed to parse command. Other commands will not be effected by a cascading parse error: {command}"
                )

        return results

    def command_names(self):
        """Return a list of all command names"""
        if not self.commandset:
            return []
        return [str(command.name) for command in self.commandset.commands]

    def split_commands_for_seperate_parsing(self, message: str) -> List[str]:
        """given a message that contains 0+ commands, return a list of strings where each string contains 1 command"""
        message = self.extract_commands_from_message(message)
        commands = [message.strip() + "}" for message in message.split("}") if message]
        return commands

    def remove_commmands_from_message(self, message: str):
        """Remove any commands from a message and return the message"""

        # commands can be on multiple lines
        command_names = "|".join(self.command_names())
        # match characters and whitespace between { }
        command_regex = r"({})\{{(.|\n)*\}}".format(command_names)
        # remove multiline commands
        message = re.sub(command_regex, "", message, flags=re.MULTILINE)

        return message

    def remove_partial_commands_from_message(self, message: str):
        """Remove any commands from a message and return the message"""

        message = message.replace("`", "")

        # remove all full command names from the message
        for command_name in self.command_names():
            message = message.replace(command_name, "")

        # remove all characters between { } including whitespace
        while "{" in message and "}" in message:
            # find index of first {
            first_open_brace_index = message.find("{")
            # find index of first }
            first_close_brace_index = message.find("}")
            # remove all characters between { } including whitespace
            message = message[:first_open_brace_index] + message[first_close_brace_index + 1 :]

        # remove all characters after { at the end of the message
        # find index of last {
        last_open_brace_index = message.rfind("{")
        # find index of last }
        last_close_brace_index = message.rfind("}")
        # if there is a { but no } then remove all characters after the {, including the {
        if last_open_brace_index > last_close_brace_index:
            message = message[:last_open_brace_index]

        # remove all { } characters
        message = message.replace("{", "").replace("}", "")

        # remove partial command names from the end of the message
        for command_name in self.command_names():
            current_substring = ""
            for char in command_name:
                current_substring += char
                message = message.rstrip(current_substring)

        return message

    def extract_commands_from_message(self, message: str) -> str:
        """Extract any commands from a message as a string"""

        message = message.replace("\n", "")
        message = message.replace("    ", "")
        message = message.replace("  ", " ")

        commands = []
        command_names = "|".join(self.command_names())
        command_regex = r"({})\{{(.*?)\}}".format(command_names)

        for match in re.finditer(command_regex, message):
            commands.append(match.group(0))

        return "\n\n".join(commands)

    def used_commands(self, message: str) -> List[Type[Command]]:
        """Count the number of commands in a message"""
        names = set()
        for command in self.commandset.commands:
            if command.name in message:
                names.add(type(command))

        return list(names)

    def count_type_usage(self, message: str) -> List[Tuple[ArgumentType, int, int]]:
        """Count the number of types in a message"""
        usage = defaultdict(int)
        first_occurance = defaultdict(int)
        all_types = set()

        all_types.update(self.commandset.type_dependencies())
        for command in self.commandset.commands:
            all_types.add(type(command))

        for t in all_types:
            if t().name in message:
                # count how many times t().name appears in the message
                usage[t] += message.count(t().name)

            # recursively add 1 for each parent class until we reach ArgumentType
            parent = t
            while parent.__bases__ and parent.__bases__[0] != ArgumentType:
                try:
                    parent = parent.__bases__[0]
                    if parent().name in message:
                        usage[parent] += message.count(parent().name)
                except Exception:
                    pass

        # for each type that is a Group, create an entry that is the sum of all its members
        all_groups = set()
        for t in all_types:
            if issubclass(t, Group):
                all_groups.add(t)

        for group in all_groups:
            usage[group] = sum([usage[member] for member in group().members])

        # filter ununsed types
        usage = {k: v for k, v in usage.items() if v > 0}

        # find the first occurance of each type
        for t in usage.keys():
            first_occurance[t] = message.find(t().name)

        full = [
            (k, v, first_occurance[k]) for k, v in sorted(usage.items(), key=lambda item: item[1])
        ]

        # return sorted by first occurance
        return sorted(full, key=lambda item: item[2])

    def count_command_usage(self, message: str) -> List[Tuple[Type[Command], int, int]]:
        """Count the number of times each command is used in a message"""
        usage = defaultdict(int)
        first_occurance = defaultdict(int)

        for command in self.commandset.commands:
            if command.name in message:
                usage[type(command)] += 1

        # filter ununsed commands
        usage = {k: v for k, v in usage.items() if v > 0}

        # find the first occurance of each command
        for command in usage.keys():
            first_occurance[command] = message.find(command().name)

        full = [
            (k, v, first_occurance[k]) for k, v in sorted(usage.items(), key=lambda item: item[1])
        ]

        # return sorted by first occurance
        return sorted(full, key=lambda item: item[2])
