# -*- coding: utf-8 -*-

from re import compile
from ..Pattern import Pattern


class CollapseWhitespace(Pattern):
	"""
	Replace each Unicode whitespace run with one space without trimming.
	"""

	def __init__(self) -> None:
		self.expression = compile(r'\s+')
		return

	def __call__(self, col: str) -> str:
		return self.expression.sub(' ', col)
