from collections import defaultdict
from dataclasses import dataclass
from typing import List, Type

from dionysus.argument_type.base import ArgumentType
from dionysus.argument_type.groups import Group
from dionysus.command.base import Command


@dataclass
class CommandSet:
    commands: list[Type[Command]] = None
    fuzzy: bool = False

    def type_dependencies(self) -> list[Type[ArgumentType]]:
        """Return a list of all types used by this command set"""
        all_types = set()
        for command in self.commands:
            all_types.update(command.type_dependencies())

        return list(all_types)

    def dependencies(self) -> list[ArgumentType]:
        """Return a list of all commands used by this command set"""
        all_types = set()
        for command in self.commands:
            all_types.update(command.dependencies())

        return list(all_types)

    @classmethod
    def from_definitions(cls, definitions: List[Type[Command]]):
        """Create a command set from a list of command definitions"""
        return cls(commands=[command() for command in definitions])

    def find_ordered_groups(self) -> list[Type[Group]]:
        """Return a list of all groups used by this command set in order of dependency where the most broad groups are first"""
        groups = defaultdict(list)

        def find_current_level(type_):
            for i, vs in groups.items():
                if type_ in vs:
                    return i

        for type_ in self.type_dependencies():
            if issubclass(type_, Group):
                if not find_current_level(type_):
                    groups[1].append(type_)

                for member in type_.members:
                    if issubclass(member, Group):
                        if not find_current_level(member):
                            groups[2].append(member)
                        else:
                            current_level = find_current_level(member)
                            groups[current_level + 1].append(member)
                            groups[current_level].remove(member)

        final_result = []
        for i in sorted(groups.keys()):
            # extend sorted by class name
            final_result.extend(sorted(groups[i], key=lambda x: x.__name__))
        return final_result

    def describe_types(self) -> str:
        """Describe the types used in this command set"""
        shown_types = set()
        all_types = self.type_dependencies()

        # skip all commands
        for command in self.commands:
            shown_types.add(type(command))

        # groups first
        group_library_description = ""
        for type_ in reversed(self.find_ordered_groups()):
            if type_ not in shown_types:
                shown_types.add(type_)
                group_library_description += f"{type_().ai_dictionary_section_header()}\n"
                for member in type_.members:
                    if not member.hide_in_ai_dictionary:
                        group_library_description += f"- {member().ai_dictionary_line()}\n"
                        shown_types.add(member)

                group_library_description += "\n"

        # then the rest
        rest_library_description = ""
        for type_ in all_types:
            if type_ not in shown_types and not type_.hide_in_ai_dictionary:
                rest_library_description += f"- {type_().ai_dictionary_line()}\n"
                shown_types.add(type_)

        return (
            f"{rest_library_description}\n{group_library_description}".strip()
            or "No types available"
        )

    def describe_commands(self) -> str:
        """Describe the commands in this command set"""
        ai_description = ""
        for command in self.commands:
            if command is Command:
                continue
            ai_description += f"- {command.ai_dictionary_line()}\n"

        return ai_description.strip()

    def describe_commands_external(self, omit_names: List[str]) -> str:
        """Describe the commands in this command set"""
        ai_description = []
        for command in self.commands:
            if command is Command:
                continue
            if command.name in omit_names:
                continue

            ai_description.append(f"{command.ai_dictionary_line_external()}".strip())

        return oxford_comma(ai_description)

    @property
    def command_names(self) -> list[str]:
        """Return a list of all command names"""
        return [command.name for command in self.commands if command is not Command]

    def command_by_name(self, name: str) -> Command:
        """Return a command by name"""
        for command in self.commands:
            if command.name == name:
                return command

        raise ValueError(f"Command {name} not found")


def oxford_comma(items: list[str]) -> str:
    """Return a string with an Oxford comma"""
    if len(items) == 0:
        return ""
    elif len(items) == 1:
        return items[0]
    elif len(items) == 2:
        return f"{items[0]} and {items[1]}"
    else:
        return f"{', '.join(items[:-1])}, and {items[-1]}"