"""Channel-neutral alert message models."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class AlertSection:
    """A headed group of message lines."""

    heading: str
    lines: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AlertMessage:
    """A formatted market alert ready for delivery through a notifier."""

    title: str
    sections: tuple[AlertSection, ...]
    footer: str
    timestamp: datetime | None
