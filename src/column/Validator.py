# -*- coding: utf-8 -*-

from .Pattern import Pattern
from typing import Tuple

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

	def __call__(self, col: str) -> str:
		for pattern in self.patterns:
			col = pattern(col)
		return col

	def __repr__(self):
		return 'Validator({})'.format(
			', '.join([repr(p) for p in self.patterns])
		)
	