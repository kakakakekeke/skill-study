#!/usr/bin/env python3
"""마켓플레이스 등록 상태를 docs/principles.md §6.4와 대조한다.

오류(exit 1): 등록 항목이 skills/ 아래 SKILL.md로 실재하지 않음, 플러그인 이름 ≠ 스킬 이름 ≠ frontmatter name,
             deprecated/ 스킬 등록, 내부 도구 등록, deprecated/README.md에 없는 폐기 스킬.
경고: skills/에 있으나 미등록인 스킬 (제작중이면 정상, 판정이 끝났다면 등록하거나 deprecated/로 옮긴다).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INTERNAL = {"gate-eval"}  # §6.4-5: 이 저장소 레이아웃에 의존하는 내부 도구


def skill_name(skill_md: Path) -> str | None:
    m = re.search(r"^name:\s*(\S+)", skill_md.read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else None


def main() -> int:
    errors, warnings = [], []
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    deprecated = {p.name for p in (ROOT / "deprecated").iterdir() if p.is_dir()} if (ROOT / "deprecated").is_dir() else set()
    registered = set()

    for p in market.get("plugins", []):
        name = p.get("name")
        src = (ROOT / p.get("source", ".")).resolve()
        paths = p.get("skills", [])
        if src != (ROOT / "skills").resolve() or len(paths) != 1:
            errors.append(f"{name}: source는 ./skills, skills는 항목 하나여야 한다")
            continue
        skill_dir = (src / paths[0]).resolve()
        md = skill_dir / "SKILL.md"
        if not md.is_file():
            errors.append(f"{name}: {md.relative_to(ROOT)} 없음")
            continue
        if not (skill_dir.name == name == skill_name(md)):
            errors.append(f"{name}: 플러그인 이름·디렉터리·frontmatter name 불일치 ({skill_dir.name}, {skill_name(md)})")
        if name in deprecated:
            errors.append(f"{name}: deprecated/에 있는 스킬은 등록 금지")
        if name in INTERNAL:
            errors.append(f"{name}: 내부 도구는 등록 금지")
        if "version" not in p:
            errors.append(f"{name}: version 없음")
        registered.add(skill_dir.name)

    readme = (ROOT / "deprecated" / "README.md")
    listed = readme.read_text(encoding="utf-8") if readme.is_file() else ""
    for d in sorted(deprecated):
        if f"`{d}`" not in listed:
            errors.append(f"deprecated/{d}: deprecated/README.md 표에 없음")

    for d in sorted((ROOT / "skills").iterdir()):
        if (d / "SKILL.md").is_file() and d.name not in registered | INTERNAL:
            warnings.append(f"skills/{d.name}: 미등록 (제작중이 아니면 등록하거나 deprecated/로 옮긴다)")

    for w in warnings:
        print(f"경고: {w}")
    for e in errors:
        print(f"오류: {e}")
    print(f"등록 {len(registered)} · 내부 {len(INTERNAL)} · 폐기 {len(deprecated)} · 오류 {len(errors)} · 경고 {len(warnings)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
