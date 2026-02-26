import logging
from typing import List, Dict, Any
import httpx
import asyncio
from .. import config

logger = logging.getLogger(__name__)


class AdzunaClient:
    BASE_URL = "https://api.adzuna.com/v1/api/jobs"

    def __init__(self, app_id: str, app_key: str, results_per_page: int = None):
        self.app_id = app_id
        self.app_key = app_key
        self.results_per_page = results_per_page or config.ADZUNA_RESULTS_PER_PAGE
        self.batch_size = config.ADZUNA_BATCH_SIZE
        self.batch_delay = config.ADZUNA_BATCH_DELAY
        self._client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )

    async def close(self):
        await self._client.aclose()

    async def search_jobs(self, what: str, country: str, where: str = "", page: int = 1) -> List[Dict[str, Any]]:

        url = f"{self.BASE_URL}/{country}/search/{page}"
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": self.results_per_page,
            "what": what
        }
        if where:
            params["where"] = where

        resp = await self._client.get(url, params=params)
        if resp.status_code != 200:
            return []
        data = resp.json()
        return data.get("results", [])

    async def search_all_jobs(self, what: str, country: str, where: str = "", max_pages: int = 50) -> List[
        Dict[str, Any]]:

        all_jobs = []
        page = 1

        url = f"{self.BASE_URL}/{country}/search/{page}"
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": self.results_per_page,
            "what": what
        }
        if where:
            params["where"] = where

        try:
            resp = await self._client.get(url, params=params)
            if resp.status_code != 200:
                return []

            data = resp.json()
            total_results = data.get("count", 0)
            results = data.get("results", [])
            all_jobs.extend(results)

            if total_results == 0:
                return []

            total_pages = min((total_results + self.results_per_page - 1) // self.results_per_page, max_pages)

            logger.info(f"Total results: {total_results}, fetching {total_pages} pages...")

            tasks = []
            for page_num in range(2, total_pages + 1):
                tasks.append(self._fetch_page(country, what, where, page_num))

                if len(tasks) >= self.batch_size:
                    batch_results = await asyncio.gather(*tasks)
                    for batch_jobs in batch_results:
                        all_jobs.extend(batch_jobs)
                    tasks = []
                    await asyncio.sleep(self.batch_delay)

            if tasks:
                batch_results = await asyncio.gather(*tasks)
                for batch_jobs in batch_results:
                    all_jobs.extend(batch_jobs)

            logger.info(f"Successfully fetched {len(all_jobs)} jobs")
            return all_jobs

        except Exception as e:
            logger.error(f"Error fetching all jobs: {e}")
            return all_jobs

    async def _fetch_page(self, country: str, what: str, where: str, page: int) -> List[
        Dict[str, Any]]:
        url = f"{self.BASE_URL}/{country}/search/{page}"
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": self.results_per_page,
            "what": what
        }
        if where:
            params["where"] = where

        try:
            resp = await self._client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("results", [])
        except Exception as e:
            logger.error(f"Error fetching page {page}: {e}")

        return []
