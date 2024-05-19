from datetime import timedelta, timezone
from typing import Type

from dateutil import parser

from dionysus.argument.base import Argument
from dionysus.argument_type.base import ArgumentType
from dionysus.argument_type.compound_argument import CompoundArgument


class Int(ArgumentType):
    hide_in_ai_dictionary = True

    def to_ai_definition(self):
        return """/-?\d+/"""

    def to_lark(self):
        return """/-?\d+/"""

    def handle_visitor(self, args, context):
        return int(args[0])


class Float(ArgumentType):
    hide_in_ai_dictionary = True

    def to_ai_definition(self):
        return """/-?\d+\.\d+/"""

    def to_lark(self):
        return """/-?\d+\.\d+/"""

    def handle_visitor(self, args, context):
        return float(args[0])


class Number(ArgumentType):
    hide_in_ai_dictionary = True

    def to_ai_definition(self):
        return "any number (ex 10 or 2.78 or -3)"

    def to_lark(self):
        return """int | float"""

    def depends_on(self) -> list[Type["ArgumentType"]]:
        return [Int, Float]

    def handle_visitor(self, args, context):
        return args[0]


class String(ArgumentType):
    def to_ai_definition(self):
        return 'String: "anything between double quotes including escape sequences"'

    def to_lark(self):
        # anything between quotes
        return """estring | /(\w|\d|\s|'|"|\/|\?|\¿|\$|:|\^|\%|\*|\&|\,|\(|\)|\[|\]|-|\–|\.)+/"""

    def handle_visitor(self, args, context):
        """parse a string from a word token"""
        if not args:
            return ""
        # Unescape the string and remove surrounding quotes
        return str(args[0]).strip().strip('"').strip("'").replace('\\"', '"')


class Stock(CompoundArgument):
    arguments: list[Argument] = [Argument("ticker", String())]

    def handle_visitor(self, args, context):
        return args["ticker"]


class Date(ArgumentType):
    """A string representing a UTC date like Date("2021-01-01") or Date("January 1st, 2021") or Date("Jan. 1st 2021"). Today and Yesterday are also valid. Always include a timezone."""

    def to_ai_definition(self):
        return "Date(<string>)"

    def to_lark(self):
        return """"Date(" string ")" """

    def depends_on(self) -> list[Type["ArgumentType"]]:
        return [String]

    def handle_visitor(self, args, context):
        from datetime import datetime
        if args[0].lower() == "today":
            return datetime.now(timezone.utc)
        if args[0].lower() == "yesterday":
            return datetime.now(timezone.utc) - timedelta(days=1)

        return parser.parse(args[0], fuzzy=True).replace(tzinfo=timezone.utc)


class Boolean(ArgumentType):
    hide_in_ai_dictionary = True

    def to_ai_definition(self):
        return "true | false"

    def to_lark(self):
        return """ /true|false|yes|no|y|n|t|f|True|False/ """

    def depends_on(self) -> list[Type["ArgumentType"]]:
        return [String]

    def handle_visitor(self, args, context):
        if args[0].lower() in ["true", "yes", "y", "t"]:
            return True

        if args[0].lower() in ["false", "no", "n", "f"]:
            return False
        return None
