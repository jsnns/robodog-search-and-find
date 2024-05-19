import unittest

from dionysus.argument.base import Argument, ArgumentType
from dionysus.argument_type.compound_argument import CompoundArgument
from dionysus.argument_type.groups import Group
from dionysus.argument_type.primative import Number
from dionysus.command.base import Command
from dionysus.commandset import CommandSet
from dionysus.parser import ChatResultParser


class TestArgumentType(unittest.TestCase):
    def test_name(self):
        class DummyArgumentType(ArgumentType):
            def to_lark(self):
                pass

            def handle_visitor(self, args, context):
                pass

        dummy_arg = DummyArgumentType()
        self.assertEqual(dummy_arg.name, "DummyArgumentType")


class TestCompoundArgument(unittest.TestCase):
    def test_depends_on(self):
        class DummyArgumentType(ArgumentType):
            def to_lark(self):
                pass

            def handle_visitor(self, args, context):
                pass

        class DummyCompoundArgument(CompoundArgument):
            arguments = [
                Argument(name="arg1", type=DummyArgumentType()),
                Argument(name="arg2", type=DummyArgumentType()),
            ]

        dummy_compound = DummyCompoundArgument()
        self.assertEqual(len(dummy_compound.depends_on()), 2)


class TestGroup(unittest.TestCase):
    def test_to_lark(self):
        class DummyArgumentTypeA(ArgumentType):
            def to_lark(self):
                return "dummy_A"

            def handle_visitor(self, args, context):
                pass

        class DummyArgumentTypeB(ArgumentType):
            def to_lark(self):
                return "dummy_B"

            def handle_visitor(self, args, context):
                pass

        class DummyGroup(Group):
            members = [DummyArgumentTypeA, DummyArgumentTypeB]

        dummy_group = DummyGroup()
        self.assertEqual(dummy_group.to_lark(), "dummy_argument_type_a | dummy_argument_type_b")
        self.assertEqual(dummy_group.name, "DummyGroup")
        self.assertEqual(dummy_group.lark_name, "dummy_group")


class TestCommandSet(unittest.TestCase):
    def test_from_definitions(self):
        class DummyCommandA(Command):
            def to_lark(self):
                pass

            def handle_visitor(self, args, context):
                pass

            def run(self, command_args, *args, **kwargs):
                pass

        class DummyCommandB(Command):
            def to_lark(self):
                pass

            def handle_visitor(self, args, context):
                pass

            def run(self, command_args, *args, **kwargs):
                pass

        command_set = CommandSet.from_definitions([DummyCommandA, DummyCommandB])
        self.assertEqual(len(command_set.commands), 2)


class TestParser(unittest.TestCase):
    def test_from_definitions(self):
        class DummyCommandA(Command):
            def handle_visitor(self, args, context):
                return {"dummy": "dummyA"}

            def run(self, command_args, *args, **kwargs):
                pass

        class DummyCommandB(Command):
            def handle_visitor(self, args, context):
                return {"dummy": "dummyB"}

            def run(self, command_args, *args, **kwargs):
                pass

        command_set = CommandSet.from_definitions([DummyCommandA, DummyCommandB])
        parser = ChatResultParser(command_set)

        message = "dummy message\nDummyCommandA{}\nDummyCommandB{}"

        result = parser(message)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["dummy"], "dummyA")
        self.assertEqual(result[1]["dummy"], "dummyB")

    def test_count_type_usage_with_groups(self):
        class DummyArgumentTypeA(ArgumentType):
            def to_lark(self):
                return "dummyArgumentTypeA"

            def handle_visitor(self, args, context):
                pass

        class DummyArgumentTypeB(ArgumentType):
            def to_lark(self):
                return "dummyArgumentTypeB"

            def handle_visitor(self, args, context):
                pass

        class DummyGroup(Group):
            members = [DummyArgumentTypeA, DummyArgumentTypeB]

        class DummyCommandA(Command):
            arguments: list[Argument] = [
                Argument(name="arg1", type=DummyGroup()),
            ]

            def handle_visitor(self, args, context):
                return {"dummy": "dummyA"}

            def run(self, command_args, *args, **kwargs):
                pass

        class DummyCommandB(Command):
            def handle_visitor(self, args, context):
                return {"dummy": "dummyB"}

            def run(self, command_args, *args, **kwargs):
                pass

        message = "dummy message\nDummyCommandA{DummyArgumentTypeA, DummyArgumentTypeB}\nDummyCommandB{}\nnDummyCommandB{}"
        parser = ChatResultParser(CommandSet.from_definitions([DummyCommandA, DummyCommandB]))

        result = parser.count_type_usage(message)

        self.assertEqual(
            [
                (DummyGroup, 2, -1),
                (DummyCommandA, 1, 14),
                (Command, 6, 19),
                (DummyArgumentTypeA, 1, 28),
                (DummyArgumentTypeB, 1, 48),
                (DummyCommandB, 2, 68),
            ],
            result,
        )

        self.assertCountEqual([DummyCommandA, DummyCommandB], parser.used_commands(message))

    def test_nested_groups(self):
        class TA(ArgumentType):
            def to_lark(self):
                return "ta"

            def handle_visitor(self, args, context):
                pass

        class TB(ArgumentType):
            def to_lark(self):
                return "tb"

            def handle_visitor(self, args, context):
                pass

        class TC(ArgumentType):
            def to_lark(self):
                return "tc"

            def handle_visitor(self, args, context):
                pass

        class GroupA(Group):
            members = [TA, TB]

        class GroupB(Group):
            members = [TC, GroupA]

        class GroupC(Group):
            members = [GroupB, GroupA]

        class DummyCommandA(Command):
            arguments: list[Argument] = [
                Argument(name="arg1", type=GroupC()),
            ]

            def handle_visitor(self, args, context):
                return {"dummy": "dummyA"}

            def run(self, command_args, *args, **kwargs):
                pass

        parser = ChatResultParser(CommandSet.from_definitions([DummyCommandA]))

        result = parser.commandset.find_ordered_groups()

        print([a.__name__ for a in result])

        self.assertListEqual(
            [GroupC, GroupB, GroupA],
            result,
        )

    def test_parser_extra_arguments(self):
        class DummyCommandA(Command):
            arguments: list[Argument] = []

            def handle_visitor(self, args, context):
                return {"dummy": "dummyA"}

            def run(self, command_args, *args, **kwargs):
                pass

        message = "dummy message\nDummyCommandA{today='2021-01-01'}"

        parser = ChatResultParser(CommandSet.from_definitions([DummyCommandA]))

        result = parser(message)

        self.assertEqual(len(result), 1)

    def test_split_commands(self):
        class DummyCommandA(Command):
            arguments: list[Argument] = []

            def handle_visitor(self, args, context):
                return {"dummy": "dummyA"}

            def run(self, command_args, *args, **kwargs):
                pass

        class DummyCommandB(Command):
            arguments: list[Argument] = []

            def handle_visitor(self, args, context):
                return {"dummy": "dummyB"}

            def run(self, command_args, *args, **kwargs):
                pass

        message = "dummy message\nDummyCommandA{}\nDummyCommandB{}"

        parser = ChatResultParser(CommandSet.from_definitions([DummyCommandA, DummyCommandB]))

        result = parser.split_commands_for_seperate_parsing(message)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], "DummyCommandA{}")
        self.assertEqual(result[1], "DummyCommandB{}")

    def test_one_malformed_command(self):
        class DummyCommandA(Command):
            arguments: list[Argument] = []

            def handle_visitor(self, args, context):
                return {"dummy": "dummyA"}

            def run(self, command_args, *args, **kwargs):
                pass

        class DummyCommandB(Command):
            arguments: list[Argument] = [Argument("number", Number())]

            def handle_visitor(self, args, context):
                return {"dummy": "dummyB"}

            def run(self, command_args, *args, **kwargs):
                pass

        message = "dummy message\nDummyCommandA{}\nDummyCommandB{number='not a number'}"

        parser = ChatResultParser(CommandSet.from_definitions([DummyCommandA, DummyCommandB]))

        result = parser(message)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["dummy"], "dummyA")
