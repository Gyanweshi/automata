"""scripts/check-wiring.py: a script nothing calls is flagged; imports, Make, skills and docs count as callers."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("check_wiring", ROOT / "scripts" / "check-wiring.py")
cw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cw)


def orphans(files: dict[str, str]) -> list[str]:
    return cw.find_orphans(list(files), read=lambda f: files[f])


def test_unreferenced_script_is_flagged_and_callers_count():
    files = {
        "scripts/lonely.py": "print('one-off')",
        "scripts/made.py": "",
        "Makefile": "made:\n\tpython scripts/made.py\n",
        "skills/x/scripts/tool.py": "",
        "skills/x/SKILL.md": "Run `python scripts/tool.py --in a`.",
        "pkg/src/pkg/helper.py": "",
        "pkg/src/pkg/user.py": "from pkg.helper import thing\n",
        "pkg/src/pkg/rel.py": "",
        "pkg/src/pkg/cli.py": "from .rel import x\nimport pkg.user\n",
        "pyproject.toml": 'pkg-cli = "pkg.cli:main"\n',
    }
    assert orphans(files) == ["scripts/lonely.py"]


def test_tests_inits_vendored_skills_and_path_lists_do_not_count():
    files = {
        "pkg/src/pkg/only_tested.py": "",
        "pkg/tests/test_only_tested.py": "from pkg.only_tested import x\n",
        "pkg/src/pkg/__init__.py": "",
        ".agents/skills/vendor/scripts/thing.py": "",
        "scripts/listed.py": "",
        ".gitignore": "scripts/listed.py\n",
    }
    assert orphans(files) == ["pkg/src/pkg/only_tested.py", "scripts/listed.py"]


def test_generic_names_need_an_import_not_a_bare_mention():
    files = {"pkg/src/pkg/cli.py": "", "README.md": "see cli.py for flags"}
    assert orphans(files) == ["pkg/src/pkg/cli.py"]


def test_repo_has_no_new_orphans():
    assert cw.main([]) == 0
