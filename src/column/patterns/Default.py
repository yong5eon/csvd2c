# -*- coding: utf-8 -*-

from typing import Union

from ..Pattern import Pattern


class Default(Pattern):
	"""
	Replace exactly empty strings with an explicitly supplied value.
	"""

	def __init__(self, value: str) -> None:
		if not isinstance(value, str):
			raise TypeError('value must be a string')
		self.value = value
		return

	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		return self.value if value == '' else value
