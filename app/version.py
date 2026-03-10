"""
Version string generator.
Format: "project-status" Ver. "version-number"+"date_month_year"-"time-24 format"-"number-of-commits-this-date"
Example: BETA Ver. 0.1103092k26-1107-2
- date_month_year: MM + DD + (year//1000) + "k" + YY (e.g. 03092k26 for 9 March 2026)
- time: 24h HHMM
- commits: git rev-list --count --after="YYYY-MM-DD 00:00:00" origin/main
"""
import subprocess
from datetime import datetime


def _commits_count_today() -> int:
    """Count git commits made today using: git rev-list --count --after="YYYY-MM-DD 00:00:00" origin/main"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        result = subprocess.run(
            [
                "git",
                "rev-list",
                "--count",
                "--after",
                f"{today} 00:00:00",
                "origin/main",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        count = int(result.stdout.strip()) if result.stdout.strip() else 0
        return max(1, count)  # at least 1 for display
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError, subprocess.TimeoutExpired):
        return 1


def _date_month_year(now: datetime) -> str:
    """Format: MM + DD + (year//1000) + 'k' + YY (e.g. 9 March 2026 -> 03092k26)."""
    m, d = now.month, now.day
    y_full = now.year
    y_century = y_full // 1000  # 2026 -> 2
    y_short = y_full % 100      # 2026 -> 26
    return f"{m:02d}{d:02d}{y_century}k{y_short:02d}"


def get_version_string(
    project_status: str = "BETA",
    version_number: str = "0.11",
) -> str:
    """
    Build version string:
    "project-status" Ver. "version-number"+"month-&-date-year"-"time-24 format"-"number-of-commits-this-date"
    Example: BETA Ver. 0.1103092k26-1107-2
    """
    now = datetime.now()
    # date_month_year (e.g. 03092k26 for 9 March 2026)
    date_month_year = _date_month_year(now)
    time_24 = now.strftime("%H%M")
    commits = _commits_count_today()
    return f"{project_status} Ver. {version_number}{date_month_year}-{time_24}-{commits}"
