"""Check the small Python hygiene contract for the demo project."""
from __future__ import annotations

import ast
from pathlib import Path

root = Path(__file__).resolve().parents[1]
failures: list[str] = []

if not (root / 'pyproject.toml').exists():
    failures.append('missing pyproject.toml')
if not (root / '.env.example').exists():
    failures.append('missing .env.example')
if (root / 'skills').resolve() != Path('/home/graham/workspace/experiments/agent-skills/skills'):
    failures.append('skills symlink does not resolve to canonical agent-skills/skills')

for path in sorted((root / 'src').rglob('*.py')) + sorted((root / 'scripts').rglob('*.py')):
    if '__pycache__' in path.parts:
        continue
    text = path.read_text()
    rel = path.relative_to(root)
    if len(text.splitlines()) > 800:
        failures.append(f'{rel}: over 800 lines')
    tree = ast.parse(text)
    if ast.get_docstring(tree) is None:
        failures.append(f'{rel}: missing module docstring')
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name == 'requests' for alias in node.names):
                failures.append(f'{rel}: imports requests instead of httpx')
        if isinstance(node, ast.ImportFrom) and node.module == 'requests':
            failures.append(f'{rel}: imports requests instead of httpx')
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == 'run' and any(kw.arg == 'shell' and isinstance(kw.value, ast.Constant) and kw.value.value is True for kw in node.keywords):
                failures.append(f'{rel}: subprocess shell=True')

if failures:
    raise SystemExit('\n'.join(failures))
print('PYTHON_STANDARDS_OK')
