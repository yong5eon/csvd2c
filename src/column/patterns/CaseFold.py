# -*- coding: utf-8 -*-

from ..Pattern import Pattern


class CaseFold(Pattern):
	"""
	Apply Unicode case folding for caseless matching.
	"""

	def __call__(self, col: str) -> str:
		return col.casefold()
