# 요구사항 명세

## 분석

GitHub 이슈 [#4: CSV reader의 escapechar 옵션 지원](./README.md#원본-이슈-본문)은 backslash로 escape된 인용부호가 들어 있는 TSV를 `strict=True`로 읽을 수 있도록 `CSV`에서 Python 표준 `csv.reader`의 `escapechar`를 설정하는 기능을 요청합니다.

현재 `src/CSV.py`의 `CSV` 생성자는 `delimiter`와 `strict`를 받지만 `escapechar`는 받지 않습니다. `open()`은 바이너리·텍스트 모드 모두에서 공통으로 `csv.reader`를 생성하며, 이때 `delimiter`와 `strict`만 전달합니다. 검증은 레코드를 파싱한 뒤 기존 row Validator, column Validator 순서로 실행됩니다. 현재 한국어·영어 사용 매뉴얼은 TSV 구분자를 안내하지만 `escapechar` 설정과 사용 예시는 안내하지 않습니다.

따라서 새 옵션을 표준 파서에 전달하고 기존 기본 동작 및 검증 흐름을 유지하는 것이 문제 해결에 필요한 최소 변경입니다. 별도 전처리나 완화된 파싱으로 우회하지 않습니다.

## 확정 요구사항

1. `CSV` 생성자에 선택적 `escapechar` 인자를 추가합니다. 인자는 현재 생성자 설정과 같이 keyword-only로 제공하고, 기본값은 `None`으로 하여 기존 호출의 파싱 동작을 유지합니다.
2. `open()`이 생성하는 표준 `csv.reader`에 설정된 `escapechar`를 전달합니다. `rb`, `r`, `rt` 모드에서 설정이 동일하게 적용되어야 합니다.
3. 이스케이프 처리를 별도로 전처리하거나 `strict`를 변경하지 않습니다. 지정한 `escapechar`의 해석과 유효성 오류는 Python 표준 `csv.reader`에 맡기며, 잘못된 설정이나 입력을 조용히 무시하지 않습니다.
4. `escapechar=None`일 때 기존 일반 CSV·TSV, `strict=True`, `doublequote` 기본 동작을 유지합니다. `doublequote` 등 이슈에서 요청하지 않은 파서 설정은 추가하지 않습니다.
5. 파싱된 레코드는 기존 처리 흐름을 따릅니다. row Validator가 먼저 적용되고 column Validator가 다음에 적용되며, reader 옵션 추가로 순서나 동작이 바뀌지 않습니다.
6. 사용자 문서의 한국어·영어판에서 옵션과 기본값을 안내하고, backslash로 escape된 인용부호를 읽는 API 예시를 제공합니다. 설명은 실제 공개 API와 일치해야 합니다.

## 제외 범위와 제약

- CSV 문법을 별도로 구현하거나 필드 값을 사전 변환하는 기능
- `strict=False`로 파싱을 완화하거나 오류를 복구·재시도하는 동작
- `doublequote` 등 추가 reader 옵션의 공개
- 원본 데이터 전체 스캔 또는 운영 데이터 적재
- 기존 Validator·Pattern의 동작이나 순서 변경

## 인수 기준

- `CSV(delimiter='\t', escapechar='\\', strict=True)` 설정으로 이슈의 합성 TSV 예시를 읽으면 데이터 행이 `['1', 'Acme "quoted" name']`으로 파싱됩니다.
- 이스케이프된 구분자, backslash 및 인용된 다중 물리행 입력의 결과가 동일 설정의 Python 표준 `csv.reader` 결과와 일치합니다.
- `escapechar`를 지정한 경우와 지정하지 않은 경우를 `rb`, `r`, `rt`에서 확인하고, 모든 읽기 모드에서 같은 파싱 설정이 적용됩니다.
- `escapechar=None` 기본값, 일반 CSV·TSV 및 `doublequote` 기본 동작이 회귀 테스트에서 유지됩니다.
- row·column Validator가 적용되는 기존 순서와 결과가 유지됩니다.
- 유효하지 않은 `escapechar` 설정은 표준 파서의 오류로 드러나며, 무시되거나 다른 설정으로 대체되지 않습니다.
- 한국어·영어 사용 문서와 API 예시에서 새 옵션, 기본값 및 사용법이 일치합니다.

## 미확정 사항

현재 이슈와 저장소 계약에서 확정되지 않은 동작은 없습니다. 잘못된 `escapechar`의 구체적인 예외 타입이나 검증 시점은 표준 `csv.reader`의 동작을 따르며, 별도 계약을 추가하지 않습니다.
