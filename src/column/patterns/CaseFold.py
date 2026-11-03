# -*- coding: utf-8 -*-

from typing import Union

from ..Pattern import Pattern


class CaseFold(Pattern):
	"""
	Apply Unicode case folding for caseless matching.
	"""

	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		return value.casefold()
