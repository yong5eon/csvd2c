# 이슈 #2: CSV iterator 프로토콜 지원

## 작업 메타데이터

| 항목 | 내용 |
| --- | --- |
| 원본 이슈 | [#2 CSV iterator 프로토콜 지원](https://github.com/yong5eon/csvd2c/issues/2) |
| 출처·작업 대상 저장소 | GitHub · `yong5eon/csvd2c` |
| 이슈 유형·레이블 | `feature` · 원본 이슈에서 확인 |
| 작업 브랜치 | 원격 작업 브랜치 `copilot/csv-iterator-support` |
| 기준 브랜치 | 기존 PR #25의 대상 `master` |
| 요구사항 | [분석·확정 명세와 인수 기준](./REQUIREMENTS.md) |
| 계획 | [변경 대상·수행 순서·검증 계획](./PLAN.md) |
| 구현 기록 | [종합 결과](./IMPLEMENTS.md) · [최신 구현](./implements/1794065037626.md) |
| 작업 기록 | [종합 결과](./TASKS.md) · [최신 검증](./tasks/1794065037626.md) |
| 판단 근거 | [최신 근거·결정](./context/1794065037626.md) |
| 변경 로그 | [고객용 변경 로그](./CHANGELOG.md) |
| 변경 적용 요청 | [PR 제목·본문](./IR.md) |

## 진행 상태

- 원본 이슈, `feature` 레이블, 원격 브랜치 및 기존 PR #25를 확인했습니다.
- `CSV` iterator를 추가하고 기존 `row()`·`rows()`와 읽기 위치·Validator 동작을 공유하도록 했습니다.
- EOF·limit, 혼합 호출, 검증 실패 후 다음 레코드, 닫힘·재오픈 동작을 테스트했습니다.
- 한국어·영어 매뉴얼과 빠른 시작, 거부 레코드 예제를 갱신했습니다.
- 관련 49개 CSV 테스트와 거부 레코드 샘플을 실행했습니다. 전체 테스트 suite 및 원격 CI는 실행하지 않았습니다.
- 비밀정보 검사에서 탐지된 항목은 없습니다. CodeQL 검토 후 최종 상태를 갱신할 예정입니다.

## 원본 이슈 본문

````markdown
## 배경

현재 `CSV.row()`는 다음 레코드 하나를 읽고, `CSV.rows()`는 남은 레코드를 generator로 제공합니다.

Python의 표준 iterator 방식인 `next(csv)`로 다음 레코드를 읽을 수 있도록 iterator 지원을 검토합니다. 행별 검증 예외를 처리하면서 다음 레코드를 읽는 사용 사례는 `samples/reject_records.py`를 참고합니다.

## 요청 내용

- `CSV`의 iterator 프로토콜 지원 검토 (`__iter__`, `__next__`)
- 열린 파일 컨텍스트에서 `next(csv)`로 다음 레코드 읽기
- 파일 끝에서 `StopIteration` 발생
- 기존 `row()`·`rows()`와 읽기 위치 및 검증 동작의 일관성 유지

## 검토 사항

- `row()` 이름 변경 여부는 별도 결정이며, 이 요청에서 변경을 확정하지 않음
- iterator 반환 형태와 생성자 Validator 적용 방식
- 닫힌 파일·재개 및 검증 실패 이후 다음 호출의 동작
- 디코딩·CSV 파싱 오류 이후 안전한 재개는 별도 문제로 구분

구체적인 설계와 구현은 후속 작업에서 확정합니다.
````

원본 이슈 댓글은 없습니다.
