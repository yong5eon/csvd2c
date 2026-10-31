# -*- coding: utf-8 -*-

from ..Pattern import Pattern
from ..Validator import Validator


class IfEmpty(Pattern):
	"""
	Run nested Patterns only for an exactly empty string.

	Nested errors propagate and are handled by the nested implementations.
	"""

	def __init__(self, *patterns: Pattern) -> None:
		self.validator = Validator(*patterns)
		return

	def __call__(self, col: str) -> str:
		return self.validator(col) if col == '' else col
