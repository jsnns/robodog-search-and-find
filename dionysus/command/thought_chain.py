from dataclasses import dataclass

from dionysus.command.result import CommandResult
from bson import ObjectId
from strenum import StrEnum


class StepStatus(StrEnum):
    Pending = "Pending"
    Final = "Final"
    Error = "Error"


class StepType(StrEnum):
    Doing = "Doing"
    Thinking = "Thinking"
    Searching = "Searching"
    Observing = "Observing"
    Remembering = "Remembering"
    Sharing = "Sharing"
    Sorting = "Sorting"
    Filtering = "Filtering"
    Reading = "Reading"
    Create = "Create"


@dataclass
class StepResult:
    """"""

    url: str = None
    label: str = None

    def to_dict(self):
        return {"url": self.url, "label": self.label}

    @classmethod
    def from_dict(cls, data):
        return cls(url=data["url"], label=data["label"])


@dataclass
class Step:
    """Base class for thought chain steps."""

    _id: ObjectId
    text: str
    action: StepType = StepType.Doing
    status: StepStatus = StepStatus.Final
    action_reference: str = None
    result: StepResult = None
    error: str = None
    """This is the error message if the step failed."""

    def summary_for_ai(self):
        if self.status == StepStatus.Final:
            return self.text

        return ""

    def user_summary(self) -> str:
        """To be shown to the user in the UI. Describes what is being done in the step."""
        return f"{self.text}"

    def to_dict(self):
        return {
            "_id": self._id,
            "text": self.text,
            "action": self.action,
            "status": self.status,
            "error": self.error,
            "action_reference": self.action_reference,
            "result": self.result.to_dict() if self.result else None,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            _id=data["_id"],
            text=data.get("text"),
            action=data.get("action"),
            status=data.get("status"),
            error=data.get("error"),
            action_reference=data.get("action_reference"),
            result=StepResult.from_dict(data["result"]) if data.get("result") else None,
        )

    @classmethod
    def do(cls, action: str):
        return cls(
            _id=ObjectId(),
            text=action,
            action=StepType.Doing,
        )

    @classmethod
    def think(cls, thought: str, status: StepStatus = StepStatus.Final):
        return cls(
            _id=ObjectId(),
            text=thought,
            action=StepType.Thinking,
            status=status,
        )

    @classmethod
    def search(cls, search: str):
        return cls(
            _id=ObjectId(),
            text=search,
            action=StepType.Searching,
        )

    @classmethod
    def observe(cls, observation: str):
        return cls(
            _id=ObjectId(),
            text=observation,
            action=StepType.Observing,
        )

    @classmethod
    def remember(cls, memory: str):
        return cls(
            _id=ObjectId(),
            text=memory,
            action=StepType.Remembering,
        )

    @classmethod
    def share(cls, share: str):
        return cls(
            _id=ObjectId(),
            text=share,
            action=StepType.Sharing,
        )

    @classmethod
    def sort(cls, sort: str):
        return cls(
            _id=ObjectId(),
            text=sort,
            action=StepType.Sorting,
        )

    @classmethod
    def filter(cls, filter: str):
        return cls(
            _id=ObjectId(),
            text=filter,
            action=StepType.Filtering,
        )

    @classmethod
    def read(cls, read: str, status: StepStatus = StepStatus.Final, reference: str = None):
        return cls(
            _id=ObjectId(),
            text=read,
            action=StepType.Reading,
            status=status,
            action_reference=reference,
        )

    @classmethod
    def create(cls, create: str, status: StepStatus = StepStatus.Final, reference: str = None):
        return cls(
            _id=ObjectId(),
            text=create,
            action=StepType.Create,
            status=status,
            action_reference=reference,
        )


class ThoughtChainStatus(StrEnum):
    Pending = "Pending"
    Final = "Final"
    Error = "Error"


@dataclass
class ThoughtChain(CommandResult):
    """Thought chains are currently just to show the user what the AI is doing. In the future, thought chains will be
    used to show the AI the AI's thought process."""

    _id: ObjectId
    steps: list[Step]
    goal: str = None
    """This is the goal of the thought chain. For example if the thought chain is about a company, a goal could be
    "Understand XYZ's business model"."""
    status: ThoughtChainStatus = ThoughtChainStatus.Pending
    final_result: str = None
    """This is the final result of the thought chain. For example if the thought chain is about a company, the final
    result could be a summary of the company's business model."""
    final_summary: str = None
    """This is the top level summary of the final result. For example if the final result is a summary of a company's
    business model, the final summary 'Understood XYZ's business model'."""
    show_ai: bool = False
    """This is a flag to show the AI's thought process to the AI in a reflective thought chain."""

    @property
    def error(self):
        """Return the full error message if the thought chain failed."""
        return "\n".join(
            [f"Step {i + 1}: {step.error}" for i, step in enumerate(self.steps) if step.error]
        )

    def full_summary(self):
        """Return the full summary of the thought chain."""
        step_summary = "\n".join(
            [f"Step {i + 1}: {step.action}" for i, step in enumerate(self.steps) if step.action]
        )

        return f"{self.goal}\n\n{step_summary}\n\nResult: {self.final_summary}"

    def summary_for_ai(self):
        if self.status == ThoughtChainStatus.Final:
            return self.final_result

        if self.status == ThoughtChainStatus.Error:
            return self.error

        return f"{self.status} {self.goal}"

    def current_status(self):
        """If pending return the first pending step. If final return the final result. If error return the error"""
        if self.status == ThoughtChainStatus.Final:
            return self.final_summary or self.goal

        return self.goal

    # helper methods
    def add_step(self, step: Step):
        """Appends step if no step with the same _id exists, otherwise replaces the existing step with the same _id."""
        for i, existing_step in enumerate(self.steps):
            if existing_step._id == step._id:
                self.steps[i] = step
                return

        self.steps.append(step)

    def get_step(self, _id: ObjectId) -> Step:
        """Returns the step with the given _id."""
        for step in self.steps:
            if step._id == _id:
                return step

        raise ValueError(f"No step with _id {str(_id)}")

    def get_step_index(self, _id: ObjectId) -> int:
        """Returns the index of the step with the given _id."""
        for i, step in enumerate(self.steps):
            if step._id == _id:
                return i

        raise ValueError(f"No step with _id {str(_id)}")

    def finalize(self, final_result: str = None, final_summary: str = None):
        if final_result:
            self.final_result = final_result

        if final_summary:
            self.final_summary = final_summary

        self.status = ThoughtChainStatus.Final

    def fail(self, error: str):
        self.status = ThoughtChainStatus.Error
        self.final_summary = error

    def to_dict(self):
        return {
            "_id": self._id,
            "steps": [step.to_dict() for step in self.steps],
            "goal": self.goal,
            "status": self.status,
            "final_result": self.final_result,
            "final_summary": self.final_summary,
            "show_ai": self.show_ai,
            "current_status": self.current_status(),
        }

    def update_step(self, reference: str, step: Step):
        """Updates the step with the given reference."""
        for i, existing_step in enumerate(self.steps):
            if existing_step.action_reference == reference:
                self.steps[i] = step
                return

    def get_step_by_reference(self, reference: str) -> Step:
        """Returns the step with the given reference."""
        for step in self.steps:
            if step.action_reference == reference:
                return step

    @classmethod
    def from_dict(cls, data):
        return cls(
            _id=data["_id"],
            steps=[Step.from_dict(step) for step in data["steps"]],
            goal=data["goal"],
            status=data["status"],
            final_result=data["final_result"],
            final_summary=data["final_summary"],
            show_ai=data["show_ai"],
        )

    @classmethod
    def new(cls, goal: str):
        return cls(_id=ObjectId(), steps=[], goal=goal)
