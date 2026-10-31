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

	class SamplePattern(Pattern):
		def __init__(self, compare):
			super(SamplePattern, self).__init__()
			self.compare = compare
			return

		def __call__(self, row: List[str]) -> List[str]:
			if not eq(row, self.compare):
				raise ValueError('{} is not equal to {}'.format(row, self.compare))
			return row  # if true, return parameter
	"""
	@abstractmethod
	def __call__(self, row: List[str]) -> List[str]:
		raise NotImplementedError('Subclasses must implement this method')

	def __repr__(self):
		return '{}()'.format(self.__class__.__name__)
