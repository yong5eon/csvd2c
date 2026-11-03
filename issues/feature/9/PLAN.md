# 읽기 범위 offset·limit 작업 계획

## 기준

[요구사항 명세](./REQUIREMENTS.md)의 R1~R8을 구현 기준으로 삼는다. 브랜치와 병합 대상은 [README](./README.md)의 메타데이터를 따른다. 커밋·푸시·병합은 별도 요청 없이 수행하지 않는다.

## 변경 대상

| 대상 | 내용 |
| --- | --- |
| `src/CSV.py` | 생성자·`open()`의 `offset`·`limit`, 값 검사, 열린 파일 단위 범위 상태, `row()`·`rows()` 공통 레코드 읽기 |
| `tests/test_range.py` | 새 범위 테스트 |
| `tests/test_samples.py` | 샘플 개수 23 → 24 |
| `samples/read_range.py` | 범위 지정 샘플 추가 |
| 문서 | `docs/README.md`·`docs/README.en.md`, 루트 `README.md`·`README.en.md`·`README.setup.md`, `samples/README.md`·`samples/README.en.md` |

`row()`·`rows()`·`header()`의 시그니처는 바꾸지 않는다.

## 수행 순서

### 1. 생성자와 open()의 범위 인자

관련 요구사항: R1·R2. 인수 기준: A1~A3.

- 생성자에 키워드 인자 `offset: int = 0`, `limit: Optional[int] = None`을 추가하고 `self.offset`, `self.limit`에 저장한다.
- `open(path, mode='rb', header=None, offset=None, limit=None)`로 확장한다. 기존 위치 인자의 순서는 유지한다.
- 값 검사 메소드 `check_range(offset, limit)`를 추가한다.
  - `bool`이거나 `int`가 아니면 `TypeError`, 음수면 `ValueError`를 발생시킨다.
  - 생성자의 `offset`은 `None`을 허용하지 않는다. 생성자의 `limit`과 `open()`의 두 인자는 `None`을 허용한다.
  - 생성자에서 호출하고, `open()`에서는 기존 `mode`·`header` 검사와 함께 파일을 열기 전에 호출한다.
- `open()`은 인자별로 `None`이면 생성자 값을, 아니면 전달 값을 사용한다. 적용 값은 `open()` 지역에서 결정하므로 재오픈 시 이전 값이 남지 않는다.

### 2. 범위 상태와 공통 레코드 읽기

선행: 1. 관련 요구사항: R3~R7. 인수 기준: A4~A10.

- 열린 파일 단위 상태 두 개를 둔다.
  - `self.skip: int`: 남은 offset 건수
  - `self.remaining: Optional[int]`: 남은 limit 건수, `None`이면 제한 없음
- `open()`에서 reader를 만든 뒤 헤더 검증보다 먼저 상태를 초기화한다. 헤더 레코드는 이 상태를 거치지 않으므로 세지 않는다. `close()`는 `skip=0`, `remaining=None`으로 초기화한다.
- `row()`와 `iterate()`가 쓰는 공통 메소드 `read_record(source)`를 추가하고, 두 곳의 `next(source)`를 이 메소드로 바꾼다.

```python
# 의사 코드 (실제 구현과 이름·세부는 다를 수 있음)
def read_record(self, source):
  if self.remaining == 0:
    raise StopIteration
  while self.skip > 0:
    next(source)
    self.skip -= 1
  record = next(source)
  if self.remaining is not None:
    self.remaining -= 1
  return record
```

- limit 검사를 offset 건너뛰기보다 먼저 하여 `limit=0`이면 offset 구간도 읽지 않는다.
- 건너뛰기 중 파일 끝의 `StopIteration`과 파싱·디코딩 오류는 그대로 전파한다. 오류가 난 레코드는 `skip`을 줄이지 않는다.
- `remaining`은 레코드를 받은 뒤, 검증 전에 줄인다. 따라서 검증 실패 레코드는 limit에 포함되고, 파싱 오류로 레코드를 받지 못한 경우는 포함되지 않는다.
- `iterate()`는 Generator 안에서 `StopIteration`을 전파할 수 없으므로(PEP 479) 기존처럼 잡아서 순회를 종료한다. 기존 reader 교체 감지는 유지한다.
- `row()`는 기존 순서(reader 확인 → 설정 결정 → 열 매핑 → 레코드 읽기 → 검증)를 유지한다. `line_num`은 읽은 레코드 기준으로 그대로 쓴다.

### 3. 테스트

선행: 2. 인수 기준: A1~A10.

`tests/test_range.py`를 추가하고 합성 CSV를 임시 디렉터리에 만들어 검증한다.

| 인수 기준 | 검증 방법 |
| --- | --- |
| A1 | 생성자·`open()`의 범위 인자 동작, `row(offset=...)`·`rows(limit=...)`가 `TypeError`인지 확인 |
| A2 | 생성자·`open()`에서 음수는 `ValueError`, `1.0`·`'1'`·`True`는 `TypeError`, 생성자 `offset=None`은 `TypeError`, `open()` 실패 시 파일을 열지 않는지 확인 |
| A3 | 생성자 값 적용, `open()` 값의 해당 오픈 한정 적용, `offset`·`limit` 독립 덮어쓰기, 재오픈 시 생성자 값과 처음부터 재계산 확인 |
| A4 | 헤더 검증기 적용 시 헤더 다음 레코드가 위치 0, 미적용 시 첫 레코드가 위치 0인지 확인 |
| A5 | 인용 개행 레코드를 1건으로 세는지 확인 |
| A6 | offset 구간에 실패하는 행·열 Validator가 호출되지 않음, offset 구간의 파싱 오류 전파, 레코드 수보다 큰 offset이 `StopIteration`·빈 순회인지 확인 |
| A7 | 검증 실패 레코드가 limit에 포함되고, limit 구간의 파싱 오류가 limit에 포함되지 않는지 확인 |
| A8 | limit 바로 다음 레코드에 파싱 오류가 있어도 발생하지 않음, `limit=0`이 offset 구간의 파싱 오류도 읽지 않는지 확인 |
| A9 | `row()` 반복, `rows()` 순회, 혼용, 검증 실패 후 `rows()` 재호출의 결과가 같은지 확인 |
| A10 | 범위 미지정 시 기존 테스트가 수정 없이 통과하는지 확인 |

파싱 오류 데이터는 `strict=True`에서 `csv.Error`를 일으키는 레코드(예: 인용 필드 뒤의 문자)로 만든다.

### 4. 샘플과 문서

선행: 3. 관련 요구사항: R8. 인수 기준: A11.

- `samples/read_range.py`: 헤더가 있는 합성 CSV를 `offset`·`limit`으로 나누어 읽고, 검증 실패 레코드도 limit에 포함되는 예를 보인다. `samples/README.md`·`README.en.md`에 등록하고 `tests/test_samples.py`의 개수를 24로 바꾼다.
- 한국어·영어 상세 매뉴얼에 읽기 범위 절을 추가한다.
  - 생성자·`open()` 인자와 적용 규칙, 생성자 `limit`을 `open()`에서 해제할 수 없는 제약
  - 헤더 유무에 따른 위치 0 예시 표
  - offset 구간의 검증 미적용·오류 전파, 검증 실패 레코드의 limit 포함, limit 도달 후 다음 레코드를 읽지 않음
  - 읽기 흐름이 이해에 도움이 되면 Mermaid 흐름도를 추가한다.
  - 목차, 사용 규칙의 `open()` 시그니처와 링크를 갱신한다.
- 루트 `README.md`·`README.en.md`·`README.setup.md`의 사용 규칙과 `open()` 시그니처에 범위 요약을 추가하고 상세 매뉴얼로 연결한다.

### 5. 검증과 기록

저장소 루트에서 실행한다.

```shell
python -m pip install --force-reinstall .
python -m unittest discover -s tests
pyright --pythonpath <검증 환경의 Python> --pythonversion 3.9 src tests samples
```

- 일반 설치본으로 전체 테스트를 실행한다. 샘플 실행 테스트를 포함한다.
- Pyright 결과를 변경 전 기준선과 비교해 신규 진단이 없는지 확인한다.
- 문서 Python 예제 실행, 상대 링크와 앵커, `git diff --check`를 확인한다.
- `implements/`·`tasks/` 단계별 기록, `IMPLEMENTS.md`·`TASKS.md`, 고객용 `CHANGELOG.md`를 작성한다.

## 호환성 주의사항

새 키워드 인자만 추가하며 기본값에서는 기존 동작과 같다. `open()`에 위치 인자로 `header`를 넘기던 호출도 그대로 동작한다. 데이터 마이그레이션이나 운영 배포는 포함하지 않는다.
