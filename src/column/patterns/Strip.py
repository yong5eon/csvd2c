# -*- coding: utf-8 -*-

from typing import Optional
from ..Pattern import Pattern


class Strip(Pattern):
	"""
	Strip leading and trailing whitespace or explicitly selected characters.
	"""

	def __init__(self, chars: Optional[str] = None) -> None:
		if chars is not None and not isinstance(chars, str):
			raise TypeError('chars must be a string or None')
		self.chars = chars
		return

	def __call__(self, col: str) -> str:
		return col.strip(self.chars)
