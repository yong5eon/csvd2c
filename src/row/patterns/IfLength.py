# -*- coding: utf-8 -*-

from typing import (
	List,
	Optional,
	Tuple,
)
from ..Pattern import Pattern
from ..Error import Error
from ..Validator import Validator
from .Length import Length


class IfLength(Pattern):
	"""
	Run nested Patterns only when the input column count matches count.

	A nested ValueError is handled by this instance's Error when provided.
	Otherwise it propagates. Handler failures are never intercepted.
	"""

	def __init__(
		self,
		count: int,
		*patterns: Pattern,
		error: Optional[Error] = None,
	) -> None:
		if error is not None and not isinstance(error, Error):
			raise TypeError('error must be a row Error instance or None')
		self.error = error
		Length(count)
		self.count = count
		self.validator = Validator(*patterns)
		self.patterns: Tuple[Pattern, ...] = patterns
		return

	def __call__(self, row: List[str]) -> List[str]:
		if len(row) != self.count:
			return row
		try:
			return self.validator(row.copy())
		except ValueError:
			if self.error is None:
				raise
		return self.error(row.copy())
