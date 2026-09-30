"""ATS scraper package."""

from .arbeitnow import fetch_arbeitnow_jobs
from .ashby import fetch_ashby_jobs
from .greenhouse import fetch_greenhouse_jobs
from .jobicy import fetch_jobicy_jobs
from .lever import fetch_lever_jobs
from .remotive import fetch_remotive_jobs
from .remotejobsfinder import fetch_remotejobsfinder_jobs
from .remoteok import fetch_remoteok_jobs
from .workday import fetch_workday_jobs

SCRAPERS = {
    "arbeitnow": fetch_arbeitnow_jobs,
    "ashby": fetch_ashby_jobs,
    "greenhouse": fetch_greenhouse_jobs,
    "jobicy": fetch_jobicy_jobs,
    "lever": fetch_lever_jobs,
    "remotive": fetch_remotive_jobs,
    "remotejobsfinder": fetch_remotejobsfinder_jobs,
    "remoteok": fetch_remoteok_jobs,
    "workday": fetch_workday_jobs,
}
