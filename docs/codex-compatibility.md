# ChatGPT 웹 Codex 호환 안내

## 구성과 호출

원본 16개 스킬·references·templates·bin·agents/researcher.md·CLAUDE.md는 보존한다.
Codex는 프로젝트 루트의 `.agents/skills/`에서 다음 이름을 발견한다:

`auto`, `career-history`, `company-research`, `cover-letter`, `experience-bank`,
`job-search`, `mock-interview`, `ncs`, `portfolio`, `resume`, `retro`, `review`,
`salary`, `scout-profile`, `strategy`, `tracker`.

같은 저장소와 이 변경이 포함된 브랜치/커밋을 선택해 **새 작업**을 열고 호출한다:

- `$auto 현재 저장소의 test/sample-data 문서를 보고 취업 준비 단계를 진단해줘.`
- `$resume test/sample-data/이력서_홍길동.md를 첨삭해줘. 없는 사실은 추가하지 마.`
- `$cover-letter 제공한 문항과 경험으로 자기소개서를 작성해줘.`
- `$company-research 네이버 백엔드 직무를 조사하고 출처와 기준일을 알려줘.`
- `$tracker 지원 현황을 보여줘.`

슬래시·언더스코어 별칭은 Claude/Telegram 전용이다. Codex는 `$cover-letter`처럼
frontmatter의 정확한 이름을 쓴다. 새 작업에서 목록이 보이지 않으면 먼저 올바른 브랜치와
`.agents/skills/<name>/SKILL.md` 체크아웃 여부를 확인한다. 이 문서는 새 웹 작업의 실제
자동 발견을 검증했다고 주장하지 않는다.

## 검토한 설치 경로

`install.sh`는 ~/.claude/skills의 동일 이름 디렉터리 삭제·심링크 생성, 에이전트 설치,
실행 권한 변경을 수행한다. `--with-insane-search`는 pip·curl_cffi 설치도 수행한다.
Codex에는 필요 없으므로 실행하지 않는다. 통합 테스트도 이 설치기를 호출하므로
이번 검증은 선택한 개별 테스트로 수행한다.

`bin/package.json`은 Node >=22, cheerio/docx/playwright/yaml을 요구하며 lifecycle scripts는 없다.
lockfile은 저장소에 없고 ignore되어 있다. 검토 후 다음처럼 설치한다(버전 범위 해석이므로
향후 동일 버전 보장은 없다). 의존성 lifecycle script 및 브라우저 다운로드를 실행하지 않는다:

```bash
cd /workspace/jobstack
npm install --prefix bin --cache /tmp/jobstack-npm-cache --ignore-scripts --no-audit --no-fund --package-lock=false
python3 tools/sync-codex-skills.py --check
```

상태는 `.jobstack/`(gitignore)이며 셸마다 JOBSTACK_STATE_DIR를 설정한다.
각 스킬의 preamble.sh는 상위 디렉터리를 찾아 기존 bin/jobstack-preamble을 실행한다.
JOBSTACK_NPM_AUTO_INSTALL=0으로 프리앰블의 묵시적 npm 설치를 막는다.
Python 3와 Bash도 사용한다. Node YAML/문서 처리 의존성을 제외하면 기본 스킬 발견·문서
읽기에는 별도의 설치나 서버가 필요 없다.

## 플랫폼 의존성과 대체·미지원 목록

| 원본 의존성 | Codex 구성 및 제한 |
| --- | --- |
| `!` 동적 셸·guardrails·bot 주입 | 명시적 프리앰블 실행·파일 읽기로 전환. bot 프로토콜은 bot 런타임에만 읽음 |
| CLAUDE_SKILL_DIR / SESSION_ID / PLUGIN_DATA | 저장소 상대 경로·선택 JOBSTACK_SESSION_ID 사용. 플러그인 저장 경로는 사용하지 않음 |
| allowed-tools, model, effort, when_to_use, argument-hint | Claude 전용 설정은 원본 보존. Codex frontmatter는 name/description만 사용. 사용 시점·입력 형식은 본문 보존. 모델·권한 강제는 미지원 |
| Bash/Read/Write/Edit/Glob/Grep/AskUserQuestion/WebSearch/WebFetch | AGENTS.md 매핑 적용. 실제 도구가 없으면 순차 조사·자료 요청. 인증·검색 권한은 자동 제공되지 않음 |
| Agent/Task + researcher 선언 | 자동 등록 안 함. 사용 가능한 위임 기능으로 JSON 계약 적용, 없으면 순차 조사. Claude 모델·maxTurns 강제 불가 |
| Claude Chrome·로그인 탭 | 현재 인증된 브라우저 도구가 있을 때만 읽기. 사용자 로컬 브라우저·로그인 세션 공유 안 됨. 없으면 본문 요청 |
| jobstack-view의 OS 브라우저·localhost | Markdown/파일 출력. 클라우드 미리보기 링크는 제공하지 않음 |
| Claude 플러그인 marketplace·install.sh·업로드 zip | 기존 기능 보존, Codex 설치에 사용하지 않음 |
| Claude 헤드리스 eval (`claude -p`) | Claude 런타임·인증·비용 필요. 이번 작업에서 실행하지 않음. Codex 도구 호출 의미 평가와 동일하다고 간주하지 않음 |
| cron/launchd·Claude Routines·Telegram 마커 | 새 클라우드 작업에 지속·등록되지 않음. 수동 1회 실행 가능. 반복 실행·봇 통합은 별도 플랫폼 설정 필요 |
| Playwright 브라우저·curl_cffi·pandoc | 선택 의존성. 브라우저 및 curl_cffi는 설치하지 않음. docx는 Node 폴백 사용. 실제 사이트 수집은 네트워크·사이트 정책·인증에 따라 다름 |

루트 원본·공유 템플릿은 삭제하거나 덮어쓰지 않는다. 사본의 references/와 scripts/를
모두 유지하며 Markdown 경로·호출 표기만 치환한다. 템플릿이 참조하는 저장소 docs/·templates/·bin/도
함께 체크아웃해야 한다. `.agents/skills`만 따로 복사한 독립 배포는 지원 범위가 아니다.

## 검증과 재생성

`python3 tools/sync-codex-skills.py`로 생성하고 `--check`로 원본 대비 드리프트를 확인한다.
이 생성기는 스킬 이름의 디렉터리 일치, 소문자·숫자·하이픈, 64자 제한,
비어 있지 않은 description과 1024자 제한, 모든 보조 파일 보존을 확인한다.
Claude용 300줄 제한은 원본에 적용하며 명시적 실행 안내가 추가된 Codex 사본에는 적용하지 않는다.

정적 검증은 LLM이 실제로 모든 단계를 올바르게 수행한다는 보장이 아니다.
웹 수집·외부 계정 접근 및 실제 이력서 작성의 의미적 품질은 이번 자동 검증에 포함하지 않는다.

### 이번 환경의 검증 결과

- Node 24.19.0, Python 3.12.14에서 의존성 설치 및 생성기 `--check` 성공.
- 16개 Codex frontmatter를 YAML 파서로 읽어 이름·description·중복·동적 주입 부재 확인.
- 16개 프리앰블 모두 격리 임시 상태에서 실제 bin 경로 탐색·상태 초기화 성공.
- 기존 기능 테스트: tracker 38, experience-bank 164, defense-map 72,
  ATS 33, export 29 검사 통과(총 336, 실패 0).
- 기존 test-skill-refs.sh 통과: 원본의 공유 참조·생성 파일 드리프트 없음.
- Claude 기반 eval, 실제 사이트 수집, 스케줄러 등록, 새 웹 작업 자동 발견은 미실행.
