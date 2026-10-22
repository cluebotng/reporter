import os
import sys
from pathlib import Path
from typing import Any

import yaml
from deepmerge import always_merger


def detect_if_running_in_test() -> bool:
    if len(sys.argv) >= 2 and sys.argv[0].endswith("manage.py") and sys.argv[1] == "test":
        return True

    return "PYTEST_VERSION" in os.environ


def _load_yaml(path: Path) -> dict[str, Any]:
    if path.is_file():
        with path.open("r") as fh:
            return yaml.load(fh, Loader=yaml.SafeLoader)
    return {}


def load_config(base_dir: Path, in_test: bool) -> dict[str, Any]:
    # Defaults
    cfg = {
        "django": {
            "secret_key": os.environ.get("DJANGO_SECRET_KEY", "development do not use"),
            "debug": False,
        },
        "mysql": {
            "default": {
                "schema": os.environ.get("TOOL_TOOLSDB_SCHEMA", "cbng_reporter"),
                "host": os.environ.get("TOOL_TOOLSDB_HOST", "tools-db"),
                "port": 3306,
                "user": os.environ.get("TOOL_TOOLSDB_USER", "cbng_reporter"),
                "password": os.environ.get("TOOL_TOOLSDB_PASSWORD"),
            },
        },
        "oauth": {
            "key": os.environ.get("CBNG_REPORT_OAUTH_KEY"),
            "secret": os.environ.get("CBNG_REPORT_OAUTH_SECRET"),
        },
        "redis": {
            "host": os.environ.get("REDIS_HOST", "redis.tool-cluebotng.svc.tools.local"),
            "port": 6379,
            "db": 2,
            "password": os.environ.get("REDIS_PASSWORD"),
        },
        "reviewer": {
            "url": os.environ.get(
                "CBNG_REVIEWER_URL", "http://cluebotng-reviewer.tool-cluebotng-review.svc.tools.local"
            ),
        },
    }

    if in_test:
        # Testing defaults
        cfg["mysql"]["default"] |= {"host": "127.0.0.1", "port": 3306}

    else:
        # Load local settings if the file exists
        cfg = always_merger.merge(cfg, _load_yaml(base_dir / "config.yaml"))

    # Load override settings
    if runtime_cfg := os.environ.get("CBNG_REPORTER_CONFIG"):
        cfg = always_merger.merge(cfg, _load_yaml(Path(runtime_cfg)))

    return cfg
