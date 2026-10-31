# -*- coding: utf-8 -*-

from ..Pattern import Pattern
from ..Validator import Validator


class IfUndecodable(Pattern):
	"""
	Run nested Patterns only when surrogateescape byte markers are present.

	Check U+DC80 through U+DCFF, not U+FFFD or other surrogate code points.
	This condition does not identify the original encoding. Nested errors
	propagate and are handled by their implementations.
	"""

	def __init__(self, *patterns: Pattern) -> None:
		self.validator = Validator(*patterns)
		return

	def __call__(self, col: str) -> str:
		if any('\udc80' <= char <= '\udcff' for char in col):
			return self.validator(col)
		return col
