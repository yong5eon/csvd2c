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
	Set,
	Tuple,
	Union,
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
		self.formats: Tuple[str, ...] = formats
		self.output = output
		return

	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		matches: Set[date] = set()
		for expression in self.formats:
			try:
				parsed: datetime = datetime.strptime(value, expression)
			except ValueError:
				continue
			matches.add(parsed.date())
		if len(matches) != 1:
			if matches:
				raise Error('Value has multiple distinct date interpretations', row, column, value)
			raise Error('Value does not match any valid complete date format', row, column, value)
		return next(iter(matches)).strftime(self.output)
