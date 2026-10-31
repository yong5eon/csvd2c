# Runnable samples

[한국어](./README.md)

These 22 standalone examples use the public csvd2c API, create small synthetic inputs, and check results with `assert`. They do not use external services, databases, or customer data.

## Running

Install the package with `pip install csvd2c` using Python 3.9 or later. Run the sample commands from the repository root containing the sample files.

```shell
pip install csvd2c
python samples/read_basic.py
python samples/column_recover_encoding.py
python samples/stream_export.py
```

Choose a file from the tables below and run it the same way. Windows CMD also accepts `/` in relative paths passed to Python. To validate all examples together:

```shell
python -m unittest discover -s tests -p "test_samples.py" -v
```

File-based samples create inputs and outputs inside a `TemporaryDirectory` and clean them up on exit. Other samples process only small in-memory values. Results and intentional errors appear in the console; existing local files are not overwritten and no network access occurs. When adapting an output example, replace temporary paths with real paths and define a retention policy.

## Example catalog

### Reading and streaming

| File | Topics |
| --- | --- |
| [read_basic.py](./read_basic.py) | `header()`, `row()`, `rows()`, EOF, preserving date-like text |
| [read_dictionary.py](./read_dictionary.py) | File headers versus output `header=`, list/dictionary output |
| [read_tsv_multiline.py](./read_tsv_multiline.py) | TSV, quoted tabs, embedded newlines, UTF-8 BOM, `rb`/`r`/`rt` |
| [detect_encoding.py](./detect_encoding.py) | Candidate order, cp949 input, ASCII ambiguity, missing-candidate errors |
| [read_overrides_close.py](./read_overrides_close.py) | Named/positional column validation, per-call overrides, `None` versus `{}`, closing and reopening |
| [stream_export.py](./stream_export.py) | UTF-8 CSV output with `csv.writer`, without accumulating the input |
| [bounded_batches.py](./bounded_batches.py) | Batches of at most 10 records, final partial batch, integration point for existing ETL storage |

### Row structures and error handling

| File | Topics |
| --- | --- |
| [row_structure.py](./row_structure.py) | `Length`, `Remove`, `Reorder`, `Insert`, `Replace`, `Slice`, preserving originals |
| [row_padding.py](./row_padding.py) | `Truncate`/`Pad` only for confirmed trailing excess or missing columns |
| [row_merge_split.py](./row_merge_split.py) | `IfLength` and `Merge` for known comma-related damage, `Split` with `maxsplit` |
| [reject_records.py](./reject_records.py) | Reject empty records, repeated headers, and length errors; log originals and reasons as JSONL |
| [custom_errors.py](./custom_errors.py) | Row/column `Error` implementations, explicit logging and approved replacement policies |
| [custom_patterns.py](./custom_patterns.py) | Row/column `Pattern` inheritance, row-before-column processing, adding provenance |

### Column cleansing and validation

| File | Topics |
| --- | --- |
| [column_text.py](./column_text.py) | Whitespace, literal/regex replacement, case transformations, Unicode normalization |
| [column_validation.py](./column_validation.py) | Required values, length, regex, choices, mapping, empty values and conditional rules |
| [column_dates.py](./column_dates.py) | Complete dates; reject missing years, invalid dates, and ambiguous formats |
| [column_numbers.py](./column_numbers.py) | Regional decimal/group separators, precision preservation, numeric ranges |
| [column_currency.py](./column_currency.py) | Multilingual aliases, damaged prefixes, constants, custom mappings, separating amounts |
| [column_currency_interval.py](./column_currency_interval.py) | Two endpoints in the provider-confirmed `VN$ amount - VN$ amount` format |
| [column_damage.py](./column_damage.py) | Surrogates, `�`, NUL, preserving ordinary question marks and multilingual text |
| [column_recode.py](./column_recode.py) | Reverse a confirmed misdecoding path with `Recode` |
| [column_recover_encoding.py](./column_recover_encoding.py) | UTF-8 `surrogateescape`, cp1258 recovery, trying the next candidate on failure |

## Adapting the examples

- Apply encoding recovery before `Strip`, replacements, or Unicode normalization. `TryRecoverEncoding` does not detect languages; the first strict decoding success wins. Permissive candidates such as cp1258 may not distinguish the actual encoding. Bytes already replaced by `�` cannot be restored.
- `Merge`, `Pad`, defaults, and currency aliases are explicit provider policies in these samples, not safe automatic repairs for every irregular CSV. `Currency` handles only prefixes; split intervals using a separate policy.
- `Date` requires year, month, and day. It does not invent years for `1-10` or `Feb-23`. `%b`/`%B` depend on the process locale, so date examples use numeric formats.
- To continue after rejected records, separate reading from validation as in [reject_records.py](./reject_records.py). Do not reuse a `rows()` generator after a validation exception. Do not guess boundaries and continue after parsing or decoding errors. Recorded numbers refer to CSV record order including the header, not physical line numbers.
- Rejection logs contain original values. For actual customer data, check storage, access control, and de-identification policies.
- For large inputs, use streaming or bounded batches rather than `list(csv.rows())`. Batch limits count records, not bytes per record. Small synthetic validation is not an actual 200GB performance test.
- Sample validation imports the installed `csvd2c` in isolated subprocesses from another working directory. Do not use `python -O`, which disables assertions.

See the [user guide](../docs/README.en.md) for complete usage rules.
