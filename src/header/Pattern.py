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
	Pattern Interface Class for Header Validator

	Sample:
	from csvd2c.header import Error

	class Rename(Pattern):
		def __init__(self, names):
			super(Rename, self).__init__()
			self.names = dict(names)
			return

		def __call__(
			self,
			value: List[str],
		) -> List[str]:
			if '' in value:
				raise Error('Header names cannot be empty', value)
			return [self.names.get(name, name) for name in value]
	"""
	@abstractmethod
	def __call__(
		self,
		value: List[str],
	) -> List[str]:
		raise NotImplementedError('Subclasses must implement this method')

	def __repr__(self):
		return '{}()'.format(self.__class__.__name__)
