# -*- coding: utf-8 -*-

from typing import (
	List,
	Tuple,
)
from ..Pattern import Pattern
from ..Validator import Validator
from .Length import Length


class IfLength(Pattern):
	"""
	Run nested Patterns only when the input column count matches count.

	Nested Patterns handle their own rejections. All nested exceptions propagate.
	"""

	def __init__(
		self,
		count: int,
		*patterns: Pattern,
	) -> None:
		Length(count)
		self.count = count
		self.validator = Validator(*patterns)
		self.patterns: Tuple[Pattern, ...] = patterns
		return

	def __call__(
		self,
		value: List[str],
		row: int,
	) -> List[str]:
		if len(value) != self.count:
			return value
		return self.validator(value, row)
