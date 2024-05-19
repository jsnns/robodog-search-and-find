import re
from typing import Type

from dionysus.command.thought_chain import Step


def format_args_for_command(args):
    """Format the arguments for a command"""
    if not isinstance(args, list):
        return args

    # each argument in the list should be a tuple with the argument name and value
    # if it isn't, return unchanged
    for arg in args:
        if not isinstance(arg, tuple) or len(arg) != 2:
            return args

    # format is likely a list of tuples (argument_name, value)
    # format as key value pairs recursively
    if len(args) > 0 and isinstance(args[0], tuple):
        return {str(k): format_args_for_command(v) for k, v in args}

    return args


def wrap_handle_visitor(func):
    """Wrap a handle_visitor function to format the arguments"""

    def wrapped(args):
        return func(format_args_for_command(args))

    return wrapped


class ArgumentType:
    parent = None
    hide_in_ai_dictionary = False

    @classmethod
    def user_thought_chain_explaination(cls) -> Step:
        """IF this is present, commands that apper in incomplete message will use this to explain why they are there"""
        return None

    def to_lark_definition(self):
        return f"{self.lark_name}: {self.to_lark()} -> {self.lark_name}"

    @property
    def name(self):
        return self.__class__.__name__

    @property
    def lark_name(self):
        """The name of this command in lark"""
        return re.sub(r"([A-Z])", r"_\1", self.name).lower().strip("_")

    @property
    def full_lark(self):
        """Includes both the argument form, the plural form, and the definition"""
        return "\n".join(
            [
                self.to_lark_definition(),
                self.lark_plural,
                self.lark_argument,
                self.lark_plural_argument,
            ]
        )

    @property
    def lark_argument(self):
        return f"""{self.lark_name}_argument: argument_name "?"? ("=" | ":") {self.lark_name}","? -> argument"""

    @property
    def lark_plural_argument(self):
        return f"""{self.lark_name}s_argument: argument_name "?"? ("=" | ":") {self.lark_name}s","? -> argument"""

    @property
    def optional_argument_names(self):
        return f"""{self.lark_name}_argument | {self.lark_name}s_argument"""

    @property
    def lark_plural(self):
        return f"""{self.lark_name}s: "[" ({self.lark_name} ",")* {self.lark_name}? "]" -> list"""

    def ai_dictionary_line(self) -> str:
        description = f" # {self.ai_explaination()}" if self.ai_explaination() else ""
        return f"{self.to_ai_definition()}{description}"

    def ai_dictionary_line_external(self) -> str:
        return f"{self.external_explaination()}"

    def ai_explaination(self) -> str:
        """details and caveats about this type"""
        # by default return the class's docstring
        return self.__doc__ or ""

    def external_explaination(self) -> str:
        """details and caveats about this type"""
        # by default return the class's docstring
        return self.__doc__ or ""

    def to_ai_definition(self):
        """the definition of this type to the AI"""
        return ""

    def to_ai_name(self):
        """the name of this type to the AI"""
        return self.name

    def to_lark(self):
        raise NotImplementedError

    def type_dependencies(self) -> list[Type["ArgumentType"]]:
        all_types = set()
        for arg in self.depends_on():
            all_types.add(arg)
        all_types.add(self.__class__)
        return list(all_types)

    def dependencies(self) -> list["ArgumentType"]:
        all_types = set()
        for arg in self.depends_on():
            all_types.add(arg())
        all_types.add(self)
        return list(all_types)

    def depends_on(self) -> list[Type["ArgumentType"]]:
        return []

    def handle_visitor(self, args, context):
        raise NotImplementedError(f"{self.__class__.__name__} does not implement handle_visitor")

    def update_context(self, args, current_context):
        return current_context

    @property
    def visitor_delegate(self):
        def visitor(args, transformer):
            current_context = getattr(transformer, "pluto_context", {})
            setattr(
                transformer,
                "pluto_context",
                {
                    **current_context,
                    **self.update_context(format_args_for_command(args), current_context),
                },
            )

            formatted_args = format_args_for_command(args)
            return self.handle_visitor(formatted_args, transformer.pluto_context)

        return visitor
