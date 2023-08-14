import functools
import re

from dataclasses import dataclass
from typing import Any, Callable

from jsno.utils import Annotation


@functools.cache
def get_class_annotations(class_) -> list[Annotation]:
    """
    Collect the class contraints of the base classes for a
    class into a mutable list. New constraints can be
    appended to the list, and will be there when this is
    called next time
    """
    return [
        annotation
        for base in class_.__bases__
        for annotation in get_class_annotations(base)
    ]


@functools.singledispatch
def get_annotation_validator(annotation):
    """
    Extendable type-indexed function that creates a validator
    function out of an annotation, if that's applicable.
    """
    return None


def get_validators(annotations):
    return [
        validator
        for annotation in annotations
        if (validator := get_annotation_validator(annotation))
    ]


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
        annotations = get_class_annotations(class_)
        annotations.append(self)
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
    """
    Constraint for a value to be in the closed range [min..max].
    Either of the bounds may be omitted.
    """

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
    """
    Constraint for the length of a value to be in the closed range
    [min..max]. Either of the bounds may be omitted.
    """

    value_name = "Length"

    def evaluate(self, value) -> bool:
        return super().evaluate(len(value))


@dataclass(slots=True, frozen=True)
class RegExConstraint(Constraint):
    """
    Constraint on a string type, matching it with a regular expression.
    The regular expression must match the _whole_ value.
    """

    name: str
    regex: re.Pattern

    def evaluate(self, value) -> bool:
        return self.regex.fullmatch(str(value)) is not None


Constraint.range = RangeConstraint  # type: ignore
Constraint.len = LenConstraint  # type: ignore


@dataclass(slots=True, frozen=True)
class FunctionConstraint(Constraint):
    """
    Constraint that is evaluated by calling the provided boolean-valued
    function on the value.
    """
    function: Callable[[Any], bool]
    name: str | None = None

    def evaluate(self, value) -> bool:
        return self.function(value)


constraint = Constraint
