# CSV iterator 프로토콜 지원 작업 계획

## 목표와 현재 상태

[요구사항 R1~R4](./REQUIREMENTS.md)에 따라 `CSV`를 반복자로 사용할 수 있게 하되 기존 `row()`·`rows()` 동작을 유지한다. 원격 작업 브랜치와 저장소 정보는 [작업 메타데이터](./README.md)를 따른다.

- 완료: 이슈·코드·테스트·문서 조사, 요구사항 및 검증 기준 확정
- 진행 예정: 메소드 구현, 테스트·예제·문서 갱신, 검증

## 변경 대상과 순서

| 대상 | 변경 내용 | 요구사항 |
| --- | --- | --- |
| `src/CSV.py` | `__iter__()`에서 `self`를 반환하고, `__next__()`에서 기존 `rows()`의 다음 결과를 사용 | R1~R3 |
| `tests/test_csv.py` | cursor 혼합 사용, Validator·limit·EOF·닫힘·재개 동작 확인 | R1~R3 |
| `samples/reject_records.py` | 다음 레코드 요청을 `next(csv)`로 변경 | R1·R3 |
| `docs/README.md`, `docs/README.en.md` | iterator 계약 및 오류·생명주기 설명 | R1~R4 |
| `README.md`, `README.en.md`, `README.setup.md` | 빠른 시작과 핵심 사용 규칙을 iterator와 일치 | R1·R4 |
| 이슈 기록 | 구현·검증 결과, 변경 로그와 적용 요청 작성 | 전체 |

### 1. Iterator 구현 및 테스트

`__iter__()`는 같은 인스턴스를 반환한다. `__next__()`는 `rows()` generator를 한 항목 진행시켜 EOF 종료와 Validator의 `StopIteration` 방지 동작을 공유한다. 이는 `row()`의 별도 이름 변경이나 읽기·검증 경로의 복제를 하지 않는다.

테스트는 `test_csv.py`의 기존 `CSVTests` 패턴을 사용한다. `next(csv)`와 `row()`·`rows()`를 섞어 offset/limit 범위의 공유를 확인하고, 검증 실패 후 다음 레코드로 이동하는지 검사한다. 닫힌 스트림, 재오픈, 정상 EOF와 limit도 확인한다.

### 2. 문서와 예제 갱신

두 언어의 상세 매뉴얼에 반복자 반환값, 열린 컨텍스트 사용, cursor 공유, EOF·닫힌 파일·검증 실패 동작을 반영한다. 세 루트 README의 빠른 시작도 `for record in csv`를 사용하고, 거부 레코드 샘플은 `next(csv)` 호출로 갱신한다. 디코딩·파싱 오류 이후 재개 보장은 추가하지 않는다.

### 3. 검증 및 정리

저장소 루트에서 `PYTHONPATH=src python -m unittest discover -s tests -p "test_csv.py" -v`와 `PYTHONPATH=src python -m unittest discover -s tests -p "test_samples.py" -v`를 실행한다. 기존 테스트와 새 테스트가 통과하면 전체 테스트는 확인된 추가 위험이 있을 때만 수행한다. `git diff --check`, 문서 링크·예제와 변경 파일 범위를 검토한다.

## 범위 밖

- `row()` 이름 변경
- 파싱·디코딩 오류 이후 안전한 재개 보장
- 의존성·빌드·테스트 도구 추가
