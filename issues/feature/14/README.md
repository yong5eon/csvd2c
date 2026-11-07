# 이슈 #14: 헤더 지정 시 레코드를 Mapping[str, str]으로 반환

## 작업 메타데이터

- 원본 이슈: [yong5eon/csvd2c#14](https://github.com/yong5eon/csvd2c/issues/14)
- 이슈 유형·레이블: `feature` (원본 이슈 적용 상태 확인)
- 작업 저장소/브랜치: `yong5eon/csvd2c` / `codex/fix-header-verification-mapping-return`
- 병합 대상: `master`
- 작업 기록: [REQUIREMENTS.md](./REQUIREMENTS.md), [PLAN.md](./PLAN.md), [IMPLEMENTS.md](./IMPLEMENTS.md), [TASKS.md](./TASKS.md), [CHANGELOG.md](./CHANGELOG.md), [IR.md](./IR.md)
- 단계별 기록: [context/1794071535691.md](./context/1794071535691.md), [implements/1794071535691.md](./implements/1794071535691.md), [tasks/1794071535691.md](./tasks/1794071535691.md)

## 이슈 요약

- 헤더 Validator를 지정한 읽기에서 `row()`·`rows()`를 `List[str]` 대신 헤더 이름 기반 `Mapping[str, str]`으로 반환
- 행/열 검증은 기존처럼 `List[str]` 기반으로 수행하고, 검증 이후 매핑 변환
- 행 검증 이후 레코드 길이가 헤더 길이와 다르면 `RowError` 발생
- 헤더 이름이 중복되거나 빈 문자열이면 `open()` 단계에서 `HeaderError`로 거부
- 정적 타입에서 반환 형태를 구분할 수 있도록 `CSV` Generic/overload 제공
- 변경에 맞춰 테스트·샘플·README·상세 매뉴얼(한/영) 동기화
