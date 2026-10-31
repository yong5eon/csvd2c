# -*- coding: utf-8 -*-

from .Pattern import Pattern
from typing import Tuple, List

__all__ = (
	'Validator',
)


class Validator(object):
	"""
	Validator Class for Row Data
	"""
	def __init__(self, *args: Pattern) -> None:
		for pattern in args:
			if not isinstance(pattern, Pattern):
				raise RuntimeError('{} must be based {}'.format(pattern, Pattern))
		self.patterns: Tuple[Pattern, ...] = args
		return

	def __call__(self, row: List[str]) -> List[str]:
		for pattern in self.patterns:
			row = pattern(row)
		return row

	def __repr__(self):
		return 'Validator({})'.format(
			', '.join([repr(p) for p in self.patterns])
		)
	