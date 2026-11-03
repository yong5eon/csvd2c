# -*- coding: utf-8 -*-

from abc import (
	ABC,
	abstractmethod,
)
from typing import List

__all__ = (
	'Pattern',
)


class Pattern(ABC):
	"""
	Pattern Interface Class for Row Validator

	Sample:
	from operator import eq
	from csvd2c.row import Error

	class SamplePattern(Pattern):
		def __init__(self, compare):
			super(SamplePattern, self).__init__()
			self.compare = compare
			return

		def __call__(
			self,
			value: List[str],
			row: int,
		) -> List[str]:
			if not eq(value, self.compare):
				raise Error('{} is not equal to {}'.format(value, self.compare), row, value)
			return value  # if true, return parameter
	"""
	@abstractmethod
	def __call__(
		self,
		value: List[str],
		row: int,
	) -> List[str]:
		raise NotImplementedError('Subclasses must implement this method')

	def __repr__(self):
		return '{}()'.format(self.__class__.__name__)
