import re

from dataclasses import dataclass
from typing import Any, Callable

from jsno.unjsonify import get_annotation_validator, get_class_annotations
from jsno.utils import Annotation


class Constraint(Annotation):
    """
    Base class for consraints
    """

    def __new__(cls, *args, **kwargs):
        if cls is Constraint:
            # Creating a plain Constraint actually creates a
            # FunctionConstraint
            cls = FunctionConstraint

        obj = object.__new__(cls)
        obj.__init__(*args, **kwargs)
        return obj

    def __or__(self, that: "Constraint") -> "Constraint":
        """
        Combining constraints with or-operator
        """
        return OrConstraint(self, that)

    @staticmethod
    def regex(regex, name=None):
        return RegExConstraint(
            name=(name or f"Regular expression {regex}"),
            regex=re.compile(regex),
        )

    def evaluate(self, value) -> bool:
        """
        To be implemented by the subclasses
        """
        raise NotImplementedError()  # pragma: no cover

    def __call__(self, class_: type) -> type:
        """
        Using the constraint as a decorator to a dataclass
        """
        print("TTT", class_, type(class_))
        existing_constraints = get_class_annotations(class_)
        existing_constraints.append(self)
        return class_

    def validate(self, value):
        if not self.evaluate(value):
            if self.name:
                message = f"Violates constraint: {self.name}"
            else:
                message = "Violates a constraint"

            raise ValueError(message)


@get_annotation_validator.register(Constraint)
def _(constraint):
    return constraint.validate


@dataclass(slots=True, frozen=True)
class OrConstraint(Constraint):
    left: Constraint
    right: Constraint

    def evaluate(self, value) -> bool:
        return self.left.evaluate(value) or self.right.evaluate(value)

    @property
    def name(self):
        return f'{self.left.name} or {self.right.name}'


@dataclass(slots=True, frozen=True)
class RangeConstraint(Constraint):
    value_name = "Value"

    min: Any | None = None
    max: Any | None = None

    def evaluate(self, value) -> bool:
        return (
            (self.min is None or value >= self.min) and
            (self.max is None or value <= self.max)
        )

    @property
    def name(self):
        if self.min is None:
            return f"{self.value_name} must be at least {self.min}"
        elif self.max is None:
            return f"{self.value_name} must be at most {self.max}"
        else:
            return f"{self.value_name} must be in range {self.min}..{self.max}"


class LenConstraint(RangeConstraint):
    value_name = "Length"

    def evaluate(self, value) -> bool:
        return super().evaluate(len(value))


@dataclass(slots=True, frozen=True)
class RegExConstraint(Constraint):
    name: str
    regex: re.Pattern

    def evaluate(self, value) -> bool:
        return self.regex.fullmatch(str(value)) is not None


Constraint.range = RangeConstraint  # type: ignore
Constraint.len = LenConstraint  # type: ignore


@dataclass(slots=True, frozen=True)
class FunctionConstraint(Constraint):
    function: Callable[[Any], bool]
    name: str | None = None

    def evaluate(self, value) -> bool:
        return self.function(value)


constraint = Constraint
