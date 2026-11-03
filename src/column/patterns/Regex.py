# -*- coding: utf-8 -*-

from re import compile
from typing import Union
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
	) -> None:
		if not isinstance(expression, str):
			raise TypeError('expression must be a string')
		self.expression = compile(expression, flags)
		return

	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		if self.expression.fullmatch(value) is None:
			raise Error('Value does not fully match the configured expression', row, column, value)
		return value
