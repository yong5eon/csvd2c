# -*- coding: utf-8 -*-

from .Pattern import Pattern
from typing import (
	Tuple,
	Union,
)

__all__ = (
	'Validator',
)


class Validator(object):
	"""
	Validator Class for Column Data
	"""
	def __init__(self, *args: Pattern) -> None:
		for pattern in args:
			if not isinstance(pattern, Pattern):
				raise RuntimeError('{} must be based {}'.format(pattern, Pattern))
		self.patterns: Tuple[Pattern, ...] = args
		return

	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		for pattern in self.patterns:
			value = pattern(value, row, column)
		return value

	def __repr__(self):
		return 'Validator({})'.format(
			', '.join([repr(p) for p in self.patterns])
		)
	