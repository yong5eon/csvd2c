# -*- coding: utf-8 -*-

from ..Pattern import Pattern


class Upper(Pattern):
	"""
	Convert Unicode text to uppercase.
	"""

	def __call__(self, col: str) -> str:
		return col.upper()
