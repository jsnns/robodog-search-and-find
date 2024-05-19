import re
from typing import List, Type

from dionysus.argument.base import Argument
from dionysus.argument_type.base import ArgumentType
from dionysus.command.thought_chain import Step


class CompoundArgument(ArgumentType):
    START = "("
    END = ")"
    arguments: List[Argument] = []

    def depends_on(self) -> list[Type["ArgumentType"]]:
        all_args = []
        for arg in self.arguments:
            all_args.extend(arg.type.type_dependencies())
        return all_args

    def to_lark(self):
        """Convert this command definition to a lark rule including all arguments"""
        arguments = " ".join([arg.to_lark() for arg in self.arguments])
        return f'"{self.name}" "{self.START}" {arguments} ignore? "{self.END}"'

    def to_ai_definition(self):
        args = ", ".join([arg.to_ai_description() for arg in self.arguments])
        return f"{self.name}{self.START}{args}{self.END}"

    def handle_visitor(self, args, context):
        return args


def class_name_to_title(class_name: str) -> str:
    """Converts a class name to a title. For example, "RSIClassName" becomes "RSI Class Name" """

    # This pattern will match uppercase letters that are either at the beginning of the string,
    # at the end of the string, or followed by other uppercase letters or a lowercase letter.
    pattern = r"((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))"

    # Replace the matches with a space and the matched character
    s = re.sub(pattern, r" \1", class_name)

    # Remove space at the beginning of the string, if any
    s = s.lstrip()

    # Capitalize the first letter of each word
    s = s.title()

    return s


class ExplainedCompoundArgument(CompoundArgument):
    prefix = None

    @classmethod
    def user_thought_chain_explaination(cls) -> Step:
        if cls.prefix is None:
            return
        return Step.create(
            f"{cls.prefix}: {class_name_to_title(cls.__name__)}",
        )
