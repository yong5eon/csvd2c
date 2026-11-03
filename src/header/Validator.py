# -*- coding: utf-8 -*-

from typing import (
	List,
	Tuple,
)
from .Pattern import Pattern

__all__ = (
	'Validator',
)


class Validator(object):
	"""
	Validator Class for Header Records

	Apply Patterns in order and return the final value as the header names.
	"""
	def __init__(self, *args: Pattern) -> None:
		for pattern in args:
			if not isinstance(pattern, Pattern):
				raise RuntimeError('{} must be based {}'.format(pattern, Pattern))
		self.patterns: Tuple[Pattern, ...] = args
		return

	def __call__(
		self,
		value: List[str],
	) -> List[str]:
		for pattern in self.patterns:
			value = pattern(value)
		return value

	def __repr__(self) -> str:
		return 'Validator({})'.format(
			', '.join([repr(p) for p in self.patterns])
		)
