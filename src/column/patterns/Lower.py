# -*- coding: utf-8 -*-

from typing import Union

from ..Pattern import Pattern


class Lower(Pattern):
	"""
	Convert Unicode text to lowercase.
	"""

	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		return value.lower()
