# -*- coding: utf-8 -*-

from typing import Union

from re import compile
from ..Pattern import Pattern
from ..Validator import Validator


class IfMatch(Pattern):
	"""
	Run nested Patterns only on a full regex match, propagating nested errors.
	"""

	def __init__(
		self,
		expression: str,
		*patterns: Pattern,
		flags: int = 0,
	) -> None:
		if not isinstance(expression, str):
			raise TypeError('expression must be a string')
		self.expression = compile(expression, flags)
		self.validator = Validator(*patterns)
		return

	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		return self.validator(value, row, column) if self.expression.fullmatch(value) is not None else value
