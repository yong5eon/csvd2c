# -*- coding: utf-8 -*-

from ..Pattern import Pattern


class Lower(Pattern):
	"""
	Convert Unicode text to lowercase.
	"""

	def __call__(self, col: str) -> str:
		return col.lower()
