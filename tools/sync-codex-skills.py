#!/usr/bin/env python3
"""원본을 보존하며 Codex 사본 생성. --check는 드리프트만 검사한다."""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CHECK = argparse.ArgumentParser()
CHECK.add_argument('--check', action='store_true')
args = CHECK.parse_args()
errors = []
skills = sorted(ROOT.glob('*/SKILL.md'))
names = [p.parent.name for p in skills]

def adapt(text, name):
    text = text.replace('$CLAUDE_SKILL_DIR/../bin/', '$_JS_BIN/')
    text = text.replace('${CLAUDE_SKILL_DIR}', f'.agents/skills/{name}')
    text = text.replace('$CLAUDE_SKILL_DIR', f'.agents/skills/{name}')
    text = text.replace('${CLAUDE_SESSION_ID}', '${JOBSTACK_SESSION_ID:-}')
    text = text.replace('Claude in Chrome 확장', '현재 제공되는 인증된 브라우저 도구')
    for other in sorted(names, key=len, reverse=True):
        text = re.sub(r'/' + other.replace('-', '_') + r'(?![\w/-])', '$' + other, text)
        text = re.sub(r'/' + re.escape(other) + r'(?![\w/-])', '$' + other, text)
    return text.rstrip() + '\n'

def emit(path, content):
    if args.check:
        if not path.is_file() or path.read_bytes() != content:
            errors.append(str(path.relative_to(ROOT)))
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

for src in skills:
    name = src.parent.name
    assert re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name) and len(name) <= 64
    raw = src.read_text()
    fm, body = raw.split('---', 2)[1:]
    assert re.search(r'^name: ' + re.escape(name) + r'$', fm, re.M)
    desc = re.search(r'^description: \|\n((?:[ \t]+.*\n)+)', fm, re.M)
    assert desc, src
    description = ' '.join(line.strip() for line in desc[1].splitlines())
    assert 0 < len(description) <= 1024
    # Claude 런타임 전용 메타데이터는 원본에 보존한다. 사용 시점·인자 정보는 본문으로 이동.
    hint = re.search(r'^argument-hint: (.*)$', fm, re.M)
    when = re.search(r'^when_to_use: \|\n((?:[ \t]+.*\n)+)', fm, re.M)
    body = re.sub(r'^!`.*`\n?', '', body, flags=re.M)
    body = re.sub(r'^> 위 실행 컨텍스트가.*\n?', '', body, flags=re.M)
    intro = f'''## Codex 실행 준비

저장소 루트에서 실행합니다. 경로는 이 SKILL.md 위치를 기준으로 저장소 루트를 찾아 해석합니다.
첫 실행 전에 `docs/codex-compatibility.md`와 이 스킬의 `references/guardrails.md`를 읽습니다.
Claude 도구명은 AGENTS.md의 Codex 대체 규칙으로 해석합니다. 동적 명령 주입은 없습니다.
설치 명령은 내용을 검토한 뒤에만 실행하며 자동 설치는 끕니다.

```bash
export JOBSTACK_STATE_DIR="${{JOBSTACK_STATE_DIR:-$PWD/.jobstack}}"
export JOBSTACK_NPM_AUTO_INSTALL=0
bash ".agents/skills/{name}/scripts/preamble.sh" {name}
```

각 후속 셸에서도 위 두 변수를 설정하고 `. "$JOBSTACK_STATE_DIR/env.sh"`를 실행합니다.
프리앰블 결과의 STATE_WRITE_FAILED=false, JS_BIN의 실제 bin 경로를 확인합니다.
bot 런타임일 때만 references/bot-protocol.md를 읽습니다. 웹 Codex에서는 cli 런타임을 사용합니다.
프리앰블의 cli/Claude 문구는 실행 환경 라벨이며 Claude 설치 요구가 아닙니다.

'''
    if hint:
        intro += '입력 형식(호출 메시지의 텍스트): ' + hint[1] + '\n\n'
    if when:
        intro += '사용 시점:\n' + when[1] + '\n'
    result = '---\nname: ' + name + '\ndescription: ' + json.dumps(description, ensure_ascii=False) + '\n---\n\n' + intro + body.lstrip()
    dest = ROOT / '.agents/skills' / name
    result = adapt(result, name)
    emit(dest / 'SKILL.md', result.encode())
    for path in sorted(src.parent.rglob('*')):
        if not path.is_file() or path == src:
            continue
        relative = path.relative_to(src.parent)
        # 보조 파일 전체 유지. Markdown의 런타임 경로·호출 표기만 변환한다.
        content = adapt(path.read_text(), name).encode() if path.suffix == '.md' else path.read_bytes()
        if relative.as_posix() in ('references/chrome-path.md', 'references/routines.md'):
            content = ('> Codex: 아래 플랫폼 고유 UI·확장·Routines는 자동 제공되지 않습니다. 실제 제공되는 도구와 인증 범위만 사용하고, 없으면 본문 붙여넣기 또는 수동 실행으로 진행합니다. 외부 계정 변경·스케줄 등록은 별도 사용자 요청이 있을 때만 수행합니다.\n\n').encode() + content
        emit(dest / relative, content)
    for ref in re.findall(r'\.agents/skills/[a-z-]+/(?:references|scripts)/[^\s`"\)]+', result):
        if not (ROOT / ref).exists() and not any(c in ref for c in '<*>…'):
            errors.append('missing reference: ' + ref)

if errors:
    print('\n'.join(errors), file=sys.stderr)
    sys.exit(1)
print(f'{len(skills)}개 스킬: 이름·description·보조 파일·생성 일관성 검증 완료')
