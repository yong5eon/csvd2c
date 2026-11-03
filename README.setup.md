# csvd2c

csvd2c stands for **CSV Dirty to Clean**. It provides streaming reads and composable validation and cleansing rules for irregular CSV and TSV data in ETL pipelines.

## Features

- Read records incrementally as lists.
- Validate the header record with an injected header Validator.
- Validate and transform row structures and individual column values.
- Normalize whitespace, Unicode, dates, numbers, and currency prefixes.
- Check encoding candidates against a file sample and recover preserved field bytes conditionally.
- Compose built-in Patterns or implement custom Patterns.

## Installation

Requires Python 3.9 or later.

```shell
pip install csvd2c
```

## Quick start

Create a UTF-8 file named `input.csv` in your execution directory:

```csv
name,date
 Example ,2026-01-10
```

```python
from csvd2c import CSV
from csvd2c.column import Validator
from csvd2c.column.patterns import (
  Required,
  Strip,
)
from csvd2c.header import Validator as HeaderValidator
from csvd2c.header.patterns import ExactOrder
from csvd2c.row import Validator as RowValidator
from csvd2c.row.patterns import Length

csv = CSV(
  encoding="utf-8",
  header=HeaderValidator(ExactOrder("name", "date")),
  row=RowValidator(Length(2)),
  column={"name": Validator(Strip(), Required())},
)

with csv.open("input.csv"):
  print(csv.header())
  for record in csv.rows():
    print(record)
```

Expected output:

```text
['name', 'date']
['Example', '2026-01-10']
```

The header Validator makes `open()` read and validate the first record as the header; `header()` returns it and `rows()` streams the remainder as lists. Named validation requires exactly one matching header column. Dates remain strings unless a Date Pattern is configured. For TSV, use `CSV(delimiter="\t")`.

## Constraints

CSV is read-only. Callers handle output storage and rejection logging. Decoding defaults to strict; decoding, parsing, and validation errors propagate without automatic record skipping.

Encoding candidate success does not identify the actual encoding. Recovery cannot restore already replaced characters. Do not accumulate the entire input or output in memory; record and batch sizes also matter. Performance on actual 200GB files has not been validated.

## License

GNU General Public License v3.0. See the LICENSE file included in the distribution. Unicode-3.0 notices for the bundled currency alias data are retained in its data module.
