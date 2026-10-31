# -*- coding: utf-8 -*-

from datetime import (
	date,
	datetime,
)
from re import (
	findall,
	fullmatch,
)
from typing import (
	Optional,
	Set,
	Tuple,
)
from ..Pattern import Pattern
from ..Error import Error


class Date(Pattern):
	"""
	Parse explicit complete dates and reject ambiguous interpretations.

	Supported directives are %Y, %y, %m, %b, %B, %d and literal %%.
	Month names depend on the process locale; %y uses Python's century rule.
	No year, month, or day is implicitly supplied.
	"""

	def __init__(
		self,
		*formats: str,
		output: str = '%Y-%m-%d',
		error: Optional[Error] = None,
	) -> None:
		if not formats:
			raise ValueError('At least one date format is required')
		for expression in (*formats, output):
			if not isinstance(expression, str):
				raise TypeError('Date formats must be strings')
			directives = findall(r'%(.)', expression)
			if fullmatch(r'(?:[^%]|%[YymbBd%])*', expression) is None:
				raise ValueError('Unsupported date directive')
		for expression in formats:
			directives = findall(r'%(.)', expression)
			if (
				sum(token in 'Yy' for token in directives) != 1
				or sum(token in 'mbB' for token in directives) != 1
				or directives.count('d') != 1
			):
				raise ValueError('Each input format must specify year, month, and day once')
		if error is not None and not isinstance(error, Error):
			raise TypeError('error must be a column Error instance or None')
		self.formats: Tuple[str, ...] = formats
		self.output = output
		self.error = error
		return

	def __call__(self, col: str) -> str:
		matches: Set[date] = set()
		for expression in self.formats:
			try:
				value: datetime = datetime.strptime(col, expression)
			except ValueError:
				continue
			matches.add(value.date())
		if len(matches) != 1:
			if self.error is not None:
				return self.error(col)
			if matches:
				raise ValueError('Value has multiple distinct date interpretations')
			raise ValueError('Value does not match any valid complete date format')
		return next(iter(matches)).strftime(self.output)
