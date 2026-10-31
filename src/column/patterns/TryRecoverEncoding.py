# -*- coding: utf-8 -*-

from .RecoverEncoding import RecoverEncoding


class TryRecoverEncoding(RecoverEncoding):
	"""
	Try a source encoding for fields containing surrogateescape byte markers.

	Return recovered Unicode text on success and the original input on codec
	failure. Fields without U+DC80 through U+DCFF pass through unchanged.
	The first successful candidate wins; no language detection is performed.

	Python standard text encodings, grouped by language or region.
	Aliases are omitted. These are candidates, not language identifiers.
	Source: https://docs.python.org/3/library/codecs.html#standard-encodings

	Language / region          Encoding candidates
	Unicode (all languages)    utf_8, utf_8_sig, utf_7, utf_16,
	                           utf_16_be, utf_16_le, utf_32,
	                           utf_32_be, utf_32_le
	Korean                     cp949, euc_kr, johab, iso2022_kr
	Japanese                   cp932, shift_jis, shift_jis_2004,
	                           shift_jisx0213, euc_jp, euc_jis_2004,
	                           euc_jisx0213, iso2022_jp, iso2022_jp_1,
	                           iso2022_jp_2004, iso2022_jp_3, iso2022_jp_ext
	Simplified Chinese         gb2312, hz
	Unified Chinese            gbk, gb18030
	Traditional Chinese        big5, big5hkscs, cp950
	Vietnamese                 cp1258
	Hebrew                     cp424, cp856, cp862, cp1255, iso8859_8
	Arabic                     cp720, cp864, cp1256, iso8859_6
	Urdu                       cp1006
	English                    ascii, cp037, cp437
	Western Europe             cp500, cp850, cp858, cp1140, cp1252,
	                           latin_1, iso8859_15, mac_roman
	Central / Eastern Europe   cp852, cp1250, iso8859_2, mac_latin2
	South-Eastern Europe       iso8859_16
	Cyrillic languages         cp855, cp1251, iso8859_5, mac_cyrillic
	Russian                    cp866, koi8_r
	Ukrainian                  cp1125, koi8_u
	Tajik                      koi8_t
	Kazakh                     kz1048, ptcp154
	Greek                      cp737, cp869, cp875, cp1253,
	                           iso8859_7, mac_greek
	Turkish                    cp857, cp1026, cp1254, iso8859_9, mac_turkish
	Baltic languages           cp775, cp1257, iso8859_13
	Northern / Nordic Europe   iso8859_4, iso8859_10
	Danish / Norwegian         cp865
	Icelandic                  cp861, mac_iceland
	Portuguese                 cp860
	Canadian                   cp863
	Thai                       cp874, iso8859_11
	Celtic languages           iso8859_14
	Esperanto / Maltese        iso8859_3
	German                     cp273
	Japanese, Korean, Chinese,
	Western Europe, Greek      iso2022_jp_2

	Do not blindly chain every candidate: overlapping byte validity means
	an earlier incorrect encoding may succeed. Stateful encodings and
	UTF-16/32 require field boundaries and codec state to be preserved;
	this Pattern does not reconstruct boundaries damaged during CSV parsing.

	read_encoding must match the original reading codec. Apply before text
	transformations. Previously replaced characters cannot be restored.
	"""

	def __init__(
		self,
		source: str,
		*,
		read_encoding: str = 'utf-8',
	) -> None:
		super().__init__(source, read_encoding=read_encoding)
		return

	def __call__(self, col: str) -> str:
		if not any('\udc80' <= char <= '\udcff' for char in col):
			return col
		try:
			raw: bytes = col.encode(self.read_encoding, errors='surrogateescape')
			return raw.decode(self.source, errors='strict')
		except UnicodeError:
			# A failed candidate deliberately leaves input intact for the next one.
			return col
