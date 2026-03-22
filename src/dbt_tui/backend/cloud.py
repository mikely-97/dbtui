"""dbt Cloud API client."""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import URLError


@dataclass
class CloudJob:
    id: int
    name: str
    project_id: int
    environment_id: int
    state: int  # 1=queued, 2=starting, 3=running, 10=success, 20=error, 30=cancelled


@dataclass
class CloudRun:
    id: int
    job_id: int
    status: int  # same as state above
    status_message: str
    duration: str
    created_at: str
    finished_at: str


@dataclass
class CloudConfig:
    api_token: str = ''
    account_id: str = ''
    base_url: str = 'https://cloud.getdbt.com/api/v2'


STATUS_LABELS = {
    1: 'Queued',
    2: 'Starting',
    3: 'Running',
    10: 'Success',
    20: 'Error',
    30: 'Cancelled',
}


class DbtCloudClient:
    """Simple dbt Cloud API client using stdlib urllib."""

    def __init__(self, config: CloudConfig):
        self.config = config

    def _request(self, endpoint: str, method: str = 'GET', data: dict | None = None) -> dict:
        url = f'{self.config.base_url}/accounts/{self.config.account_id}/{endpoint}'
        headers = {
            'Authorization': f'Token {self.config.api_token}',
            'Content-Type': 'application/json',
        }
        body = json.dumps(data).encode() if data else None
        req = Request(url, data=body, headers=headers, method=method)
        try:
            with urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except URLError as e:
            return {'status': {'code': 0}, 'error': str(e)}

    def list_jobs(self) -> list[CloudJob]:
        resp = self._request('jobs/')
        jobs = []
        for j in resp.get('data', []):
            jobs.append(CloudJob(
                id=j['id'],
                name=j.get('name', ''),
                project_id=j.get('project_id', 0),
                environment_id=j.get('environment_id', 0),
                state=j.get('state', 0),
            ))
        return jobs

    def get_run(self, run_id: int) -> CloudRun | None:
        resp = self._request(f'runs/{run_id}/')
        d = resp.get('data')
        if not d:
            return None
        return CloudRun(
            id=d['id'],
            job_id=d.get('job_id', 0),
            status=d.get('status', 0),
            status_message=d.get('status_message', ''),
            duration=d.get('duration', ''),
            created_at=d.get('created_at', ''),
            finished_at=d.get('finished_at', ''),
        )

    def trigger_run(self, job_id: int, cause: str = 'Triggered from dbt-tui') -> int | None:
        """Trigger a job run. Returns run_id or None."""
        resp = self._request(f'jobs/{job_id}/run/', method='POST', data={'cause': cause})
        data = resp.get('data')
        return data['id'] if data else None

    def list_recent_runs(self, limit: int = 10) -> list[CloudRun]:
        resp = self._request(f'runs/?limit={limit}&order_by=-id')
        runs = []
        for d in resp.get('data', []):
            runs.append(CloudRun(
                id=d['id'],
                job_id=d.get('job_id', 0),
                status=d.get('status', 0),
                status_message=d.get('status_message', ''),
                duration=d.get('duration', ''),
                created_at=d.get('created_at', ''),
                finished_at=d.get('finished_at', ''),
            ))
        return runs
