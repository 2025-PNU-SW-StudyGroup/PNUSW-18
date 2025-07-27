from typing import Tuple

from domains.common.types import TermUnit


def parse_amount_range(text: str) -> Tuple[int, int, TermUnit]:
    return (0, 0, "month")


def parse_term_range(text: str) -> Tuple[int, int, TermUnit]:
    return (1, 12, "month")
