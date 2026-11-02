# 이슈 #4: CSV reader의 escapechar 옵션 지원

## 작업 메타데이터

| 항목 | 내용 |
| --- | --- |
| 원본 이슈 | [#4 CSV reader의 escapechar 옵션 지원](https://github.com/yong5eon/csvd2c/issues/4) |
| 출처 | GitHub · `yong5eon/csvd2c` |
| 이슈 유형·레이블 | `feature` · 원본 이슈에 적용 확인 |
| 작업 브랜치 | `feature/4` |
| 기준 브랜치 | `master` |
| 병합 대상 브랜치 | 미확정 |
| 요구사항 | [요구사항 명세](./REQUIREMENTS.md) |
| 계획 | [작업 계획](./PLAN.md) |
| 작업 기록 | [종합 기록](./TASKS.md) · [최신 단계별 기록](./tasks/1793634865397.md) |

## 현재 구현과 요청의 차이

- [`src/CSV.py`](../../../src/CSV.py)의 `CSV` 생성자는 `delimiter`와 `strict`를 받지만 `escapechar`는 받지 않으며, `open()`도 `csv.reader`에 해당 옵션을 전달하지 않습니다.
- 한국어·영어 [사용 매뉴얼](../../../docs/README.md)과 [영어 사용 매뉴얼](../../../docs/README.en.md)은 TSV 구분자와 `strict` 파싱을 안내하지만 `escapechar` 설정은 안내하지 않습니다.

## 원본 이슈 본문

원본 본문은 아래에 그대로 보존합니다.

````markdown
## 목적

`CSV`에서 Python 표준 `csv.reader`의 `escapechar` 옵션을 지정할 수 있도록 지원 요청

현재 `delimiter='\t'`로 TSV는 읽을 수 있지만, backslash로 escape된 인용부호가 포함된 레코드는 기본 `escapechar=None`으로 인해 엄격 파싱에 실패합니다. csvd2c의 reader·Validator·Pattern을 그대로 사용하려는 목적입니다.

## 현재 동작

현재 기본 브랜치의 `src/CSV.py`에서 생성자는 `delimiter`, `strict`를 제공하지만 `escapechar`는 받지 않습니다. `open()`의 `csv.reader` 생성에도 전달하지 않습니다.

## 합성 데이터 재현

실제 데이터나 개인 경로를 포함하지 않는 예시입니다.

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from csvd2c import CSV

with TemporaryDirectory() as directory:
    source = Path(directory) / 'escaped.tsv'
    quote = chr(34)
    escaped_quote = chr(92) + quote
    name = quote + 'Acme ' + escaped_quote + 'quoted' + escaped_quote + ' name' + quote
    source.write_text('id\tname\n1\t' + name + '\n', encoding='utf-8')
    with CSV(delimiter='\t', strict=True).open(str(source)) as data:
        data.header()
        print(list(data.rows()))
```

현재는 escape된 인용부호 뒤에서 `csv.Error`가 발생합니다. 원하는 파싱 값은 `['1', 'Acme "quoted" name']`입니다.

## 요청 범위

- `CSV` 생성자에 선택적 `escapechar` 인자 추가
- 기본값은 `None`으로 유지해 기존 CSV 호출의 동작 보존
- `open()`이 만드는 `csv.reader`에 지정한 값을 전달
- `CSV(delimiter='\t', escapechar='\\', strict=True)`로 위 입력 파싱 지원
- 이스케이프를 별도 전처리로 지우거나 `strict=False`로 완화하지 않고 표준 파서 계약 유지
- 관련 한국어·영어 사용 문서와 API 예시 갱신

## 검증 기준

- backslash로 escape된 인용부호를 포함한 TSV의 필드 값 정확성
- 이스케이프된 구분자·backslash와 인용된 다중 물리행 입력의 표준 `csv.reader` 결과 대조
- 기존 `escapechar=None` 기본값, 일반 CSV, `doublequote` 기본 동작의 회귀 확인
- `open()`의 바이너리/텍스트 모드에 같은 설정 적용
- 기존 row/column Validator·Pattern 적용 순서 유지
- 유효하지 않은 `escapechar` 입력은 오류로 알리고 묵인하지 않음

원본 전체 스캔이나 운영 적재는 이 요청 범위에 포함하지 않습니다.
````
