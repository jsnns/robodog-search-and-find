from typing import Type
from dionysus.argument_type.base import ArgumentType


class Group(ArgumentType):
    members: list[Type["ArgumentType"]] = None

    def ai_dictionary_section_header(self):
        return f"## Valid {self.name} ({self.__doc__ or 'only use these'}):"

    def type_dependencies(self) -> list[Type["ArgumentType"]]:
        all_types = super().type_dependencies()

        for member in self.members:
            all_types.extend(member().type_dependencies())
            all_types.append(member)

        return all_types

    def dependencies(self) -> list[ArgumentType]:
        all_types = super().dependencies()

        for member in self.members:
            all_types.extend(member().dependencies())
            all_types.append(member)

        return all_types

    def to_lark(self):
        return f"{' | '.join([type().lark_name for type in self.members])}"

    def to_ai_definition(self):
        return f"{self.name}"

    def handle_visitor(self, args, context):
        return args[0]
