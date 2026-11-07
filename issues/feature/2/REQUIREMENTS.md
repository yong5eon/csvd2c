# CSV iterator 프로토콜 지원 요구사항

## 목적과 범위

[원본 이슈](./README.md)의 요청에 따라 열린 파일에서 `next(csv)`로 레코드를 읽을 수 있도록 `CSV`의 표준 iterator 프로토콜을 지원한다. 기존 `row()`·`rows()` API는 유지하고 이들과 읽기 위치 및 검증을 공유한다.

## 분석과 근거

- [CSV 구현](../../../../src/CSV.py)의 `row()`는 `require_reader()`를 통해 열린 reader를 확인하고, 생성자 또는 호출별 Validator를 선택해 `read_record()`와 공통 `validate()`를 실행한다.
- `read_record()`는 `offset`·`limit`을 처리하고, 레코드를 얻으면 검증 전에 원문을 저장하고 limit을 감소시킨다. 검증 실패 뒤에도 reader 위치가 다음 레코드를 가리킨다.
- `rows()`는 같은 `read_record()`·`validate()` 흐름을 사용하며, EOF와 limit에서는 정상적으로 종료한다. 검증 도중 Validator가 직접 `StopIteration`을 발생시키면 generator 규칙에 따라 `RuntimeError`가 발생한다.
- `close()`는 reader를 무효화하고 읽기 상태를 초기화한다. 다시 `open()`하면 새 읽기 상태를 시작한다.
- `samples/reject_records.py`는 `row()`의 반복 호출과 행·컬럼 검증 실패 처리를 보여 준다. 이 사용 흐름은 `next(csv)`로도 제공할 수 있다.

이에 따라 `iter(csv)`는 `csv` 자신을 반환하고, `__next__()`는 기존 `rows()`의 단일 항목을 요청하도록 한다. 그러면 읽기 범위와 Validator 선택을 재구현하지 않고 generator의 EOF 및 Validator의 `StopIteration` 처리를 그대로 재사용한다. `row()`의 이름이나 기존 `row()`·`rows()` 동작은 변경하지 않는다.

## 확정 요구사항

### R1. Iterator 프로토콜

- `CSV`는 `__iter__()`와 `__next__()`를 제공한다.
- `iter(csv)`는 동일한 `CSV` 인스턴스를 반환한다.
- 열린 파일 컨텍스트에서 `next(csv)`는 다음 레코드를 list로 반환한다.
- 생성자의 행·컬럼 Validator를 `rows()`와 같은 순서와 규칙으로 적용한다.

### R2. 읽기 위치와 종료

- `next(csv)`, `row()` 및 `rows()`는 같은 reader·offset·limit 상태를 공유한다.
- `next(csv)`는 EOF 또는 limit 도달 시 `StopIteration`을 발생시킨다.
- 닫힌 파일이나 아직 열지 않은 파일에서 `next(csv)`는 기존 `row()`·`rows()`와 같이 `RuntimeError`를 발생시킨다.
- 닫힌 뒤 다시 연 경우 새 파일 컨텍스트의 읽기 상태에서 시작한다. iterator는 `CSV` 인스턴스 자체이므로 별도 generator를 재사용하지 않는다.

### R3. 검증 및 읽기 오류

- 행·컬럼 검증 오류는 전파한다. 레코드는 검증 전에 소비되므로 검증 실패 뒤 다음 `next(csv)`는 다음 레코드를 읽는다.
- `Validator`에서 발생한 `StopIteration`은 iterator의 EOF로 오인되지 않으며 `rows()`와 동일하게 `RuntimeError`로 처리한다.
- 디코딩·CSV 파싱 오류는 기존처럼 전파한다. 그 오류 뒤 스트림을 안전하게 재개하는 기능은 범위에 포함하지 않는다.

### R4. 호환성과 문서

- `row()`와 `rows()`의 서명·기존 사용법을 유지한다.
- 한국어·영어 사용자 문서, 패키지 빠른 시작 및 `reject_records.py` 예제에서 iterator 사용법을 안내한다.

## 인수 기준

| 요구사항 | 검증 기준 |
| --- | --- |
| R1 | `iter(csv) is csv`; `next(csv)`에서 레코드 및 생성자 Validator 결과 확인 |
| R2 | `next(csv)`와 `row()`·`rows()` 혼합 호출의 순서, limit 및 EOF의 `StopIteration` 확인 |
| R2 | 열린 컨텍스트 외부에서 `RuntimeError`, 재오픈 시 처음부터 읽기 확인 |
| R3 | 검증 예외 전파, 실패 레코드의 소비 및 다음 `next(csv)`로 재개 확인 |
| R3 | Validator의 `StopIteration`이 EOF로 오인되지 않으며 디코딩·파싱 오류 회귀 확인 |
| R4 | 기존 CSV·샘플 테스트 통과, 한국어·영어 매뉴얼과 공개 예제의 동작 일치 확인 |
