# -*- coding: utf-8 -*-

from typing import Union

from re import compile
from ..Pattern import Pattern


class CollapseWhitespace(Pattern):
	"""
	Replace each Unicode whitespace run with one space without trimming.
	"""

	def __init__(self) -> None:
		self.expression = compile(r'\s+')
		return

	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		return self.expression.sub(' ', value)
