# -*- coding: utf-8 -*-

from re import compile
from ..Pattern import Pattern


class RegexReplace(Pattern):
	"""
	Replace regex matches; count zero means all matches, as in re.sub.
	"""

	def __init__(
		self,
		expression: str,
		replacement: str,
		*,
		count: int = 0,
		flags: int = 0,
	) -> None:
		if not isinstance(expression, str) or not isinstance(replacement, str):
			raise TypeError('expression and replacement must be strings')
		if type(count) is not int or count < 0:
			raise ValueError('count must be a nonnegative integer')
		self.expression = compile(expression, flags)
		# Validate replacement escapes and group references at construction.
		self.expression.sub(replacement, '')
		self.replacement = replacement
		self.count = count
		return

	def __call__(self, col: str) -> str:
		return self.expression.sub(self.replacement, col, count=self.count)
