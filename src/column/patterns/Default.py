# -*- coding: utf-8 -*-

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

	def __call__(self, col: str) -> str:
		return self.value if col == '' else col
