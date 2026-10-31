# -*- coding: utf-8 -*-

from re import compile
from typing import Optional
from ..Pattern import Pattern
from ..Error import Error


class Regex(Pattern):
	"""
	Require a full regex match and return the input unchanged.
	"""

	def __init__(
		self,
		expression: str,
		*,
		flags: int = 0,
		error: Optional[Error] = None,
	) -> None:
		if not isinstance(expression, str):
			raise TypeError('expression must be a string')
		if error is not None and not isinstance(error, Error):
			raise TypeError('error must be a column Error instance or None')
		self.expression = compile(expression, flags)
		self.error = error
		return

	def __call__(self, col: str) -> str:
		if self.expression.fullmatch(col) is None:
			if self.error is not None:
				return self.error(col)
			raise ValueError('Value does not fully match the configured expression')
		return col
