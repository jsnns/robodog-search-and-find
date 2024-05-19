from dataclasses import dataclass


class CommandResult:
    pass


@dataclass
class CommandResults:
    results: list[CommandResult]

    def __iter__(self):
        return iter(self.results)

    def __getitem__(self, item):
        return self.results[item]

    def __len__(self):
        return len(self.results)

    def __add__(self, other):
        return CommandResults(self.results + other.results)

    def __iadd__(self, other):
        self.results += other.results
        return self

    def __repr__(self):
        return f"CommandResults({self.results})"

    def __str__(self):
        return f"CommandResults({self.results})"

    def __eq__(self, other):
        return self.results == other.results

    def __hash__(self):
        return hash(self.results)

    def __contains__(self, item):
        return item in self.results

    def __bool__(self):
        return bool(self.results)

    def like(self, type):
        return CommandResults([result for result in self.results if isinstance(result, type)])
