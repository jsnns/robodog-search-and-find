from dataclasses import dataclass
from dionysus.argument_type.base import ArgumentType


@dataclass
class Argument:
    """A command argument definition"""

    name: str
    type: ArgumentType
    required: bool = True
    description: str = None
    multiple: bool = False
    choices: list[str] = None

    def to_ai_description(self):
        quoted_choices = [f'"{choice}"' for choice in self.choices] if self.choices else []
        return f"{self.name}{'' if self.required else '?'}: {' | '.join(quoted_choices) if self.choices else self.type.name}{'[]' if self.multiple else ''}"

    def to_lark(self):
        """Convert this command argument definition to fragment of a lark rule"""
        return f'{self.type.lark_name}{"s" if self.multiple else ""}_argument{"" if self.required else "?"}'
