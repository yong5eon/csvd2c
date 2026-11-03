# -*- coding: utf-8 -*-

from typing import Union

from ..Pattern import Pattern


class Upper(Pattern):
	"""
	Convert Unicode text to uppercase.
	"""

	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		return value.upper()
