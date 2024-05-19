from dataclasses import dataclass
from typing import Callable

from dionysus.commandset import CommandSet

@dataclass
class PromptTemplate:
    """A prompt for the AI."""

    identity: str = None
    response_format: str = None
    rules: list = None
    command_set: CommandSet = None
    dictionary: dict = None
    variables: list[str] = None
    generate_for_user: Callable[[str], str] = None

    @property
    def ruleset(self) -> str:
        if not self.rules:
            return ""
        return "\n".join([f"- {rule}" for rule in self.rules])

    @property
    def words(self) -> str:
        """Convert dict to a dictionary string."""
        return "\n".join([f"- {key}: {value}" for key, value in (self.dictionary or {}).items()])

    def as_system_message(self, user_id: str = None) -> str:
        return self.__str__(user_id=user_id)

    def __call__(self, *args, **kwargs) -> str:
        return str(self)

    def __str__(self, user_id: str = None) -> str:
        """Returns the prompt as a string."""
        from datetime import datetime
        prompt = f"\n\nThe current date and time is {datetime.now().strftime('%m/%d/%Y, %H:%M:%S')}."

        if self.identity:
            prompt += f"\nYour identity: {self.identity}"

        if self.response_format:
            prompt += f"\n\nResponse format: {self.response_format}"

        if self.command_set and self.command_set.commands:
            prompt += (
                "\n\nYou will be provided with types and commands, they represent a DSL. It's a declarative language and does not support language features like expressions, variables, templates, or similar. If you cannot accomplish the request with the provided DSL always respond "
                + (
                    "with 'pass'."
                    if not self.command_set.fuzzy
                    else "by interpreting the request in a way that is compatible with the provided DSL. In your response rewrite the request and then provide the solution without further questions."
                )
            )
            prompt += f"\n\n# Type library:\n{self.command_set.describe_types()}\n\n# Command library (must be alone on a new line):\n{self.command_set.describe_commands()}"

        if self.generate_for_user and user_id:
            prompt += f"\n\n{self.generate_for_user(user_id)}"

        if self.dictionary:
            prompt += f"\n\nHere are some words and phrases you may need to use:\n{self.words}"

        if self.rules:
            prompt += f"\n\nYour rules:\n{self.ruleset}"

        return prompt.strip()
