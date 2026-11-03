# -*- coding: utf-8 -*-

from typing import Union

from ..Pattern import Pattern


class Replace(Pattern):
	"""
	Replace literal substrings using str.replace, including empty substrings.
	"""

	def __init__(
		self,
		old: str,
		new: str,
		count: int = -1,
	) -> None:
		if not isinstance(old, str) or not isinstance(new, str):
			raise TypeError('old and new must be strings')
		if type(count) is not int:
			raise TypeError('count must be an integer')
		self.old = old
		self.new = new
		self.count = count
		return

	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		return value.replace(self.old, self.new, self.count)
