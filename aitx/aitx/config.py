"""Study-wide settings. Edit these before running."""
from dataclasses import dataclass, field
import os


@dataclass
class Config:
    # SEC requires a descriptive User-Agent with a contact e-mail.
    # https://www.sec.gov/os/accessing-edgar-data
    user_agent: str = os.environ.get("AITX_USER_AGENT", "")
    start_date: str = "2023-01-01"
    end_date: str = "2026-09-29"      # censoring date
    base_year: int = 2022             # year for pre-determined financials (exclusion rules)
    min_assets_usd: float = 10e6      # rule R3
    forms: tuple = ("10-K", "10-Q", "8-K")
    sec_rps: float = 8.0              # SEC fair-access limit is 10 requests/second
    cc_rps: float = 1.0               # be gentle with the Common Crawl index server
    data_dir: str = "data"
    cache_dir: str = field(default_factory=lambda: os.path.join("data", "cache"))

    def check(self):
        if "@" not in self.user_agent:
            raise SystemExit(
                "Set AITX_USER_AGENT to 'Your Name your.email@university.edu' "
                "(SEC rejects requests without a contact e-mail)."
            )
