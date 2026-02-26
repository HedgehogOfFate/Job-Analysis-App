import pytest
from unittest.mock import patch, Mock, AsyncMock, PropertyMock
from app.clients.adzuna_client import AdzunaClient


class TestClientInitialization:

    def test_client_creation(self):
        client = AdzunaClient("test_id", "test_key", results_per_page=25)

        assert client.app_id == "test_id"
        assert client.app_key == "test_key"
        assert client.results_per_page == 25

    def test_client_default_results_per_page(self):
        with patch('app.clients.adzuna_client.config.ADZUNA_RESULTS_PER_PAGE', 50):
            client = AdzunaClient("test_id", "test_key")
            assert client.results_per_page == 50

    def test_client_has_shared_http_client(self):
        client = AdzunaClient("test_id", "test_key")
        assert client._client is not None

    def test_client_batch_config(self):
        with patch('app.clients.adzuna_client.config.ADZUNA_BATCH_SIZE', 10), \
             patch('app.clients.adzuna_client.config.ADZUNA_BATCH_DELAY', 0.1):
            client = AdzunaClient("test_id", "test_key")
            assert client.batch_size == 10
            assert client.batch_delay == 0.1


class TestSinglePageSearch:

    @pytest.mark.asyncio
    async def test_search_jobs_success(self, mock_api_response):
        client = AdzunaClient("test_id", "test_key")
        client._client = AsyncMock()
        client._client.get.return_value = mock_api_response

        jobs = await client.search_jobs("Developer", "gb", "London")

        assert len(jobs) == 1
        assert jobs[0]["title"] == "Test Job"

    @pytest.mark.asyncio
    async def test_search_jobs_with_location(self, mock_api_response):
        client = AdzunaClient("test_id", "test_key")
        client._client = AsyncMock()
        client._client.get.return_value = mock_api_response

        await client.search_jobs("Developer", "gb", "London")

        call_kwargs = client._client.get.call_args[1]
        assert "where" in call_kwargs["params"]
        assert call_kwargs["params"]["where"] == "London"

    @pytest.mark.asyncio
    async def test_search_jobs_without_location(self, mock_api_response):
        client = AdzunaClient("test_id", "test_key")
        client._client = AsyncMock()
        client._client.get.return_value = mock_api_response

        await client.search_jobs("Developer", "gb")

        call_kwargs = client._client.get.call_args[1]
        assert "where" not in call_kwargs["params"] or call_kwargs["params"]["where"] == ""

    @pytest.mark.asyncio
    async def test_search_jobs_correct_url(self, mock_api_response):
        client = AdzunaClient("test_id", "test_key")
        client._client = AsyncMock()
        client._client.get.return_value = mock_api_response

        await client.search_jobs("Developer", "gb")

        call_args = client._client.get.call_args[0]
        url = call_args[0]
        assert "api.adzuna.com" in url
        assert "/gb/search/" in url

    @pytest.mark.asyncio
    async def test_search_jobs_api_error(self, mock_api_error):
        client = AdzunaClient("test_id", "test_key")
        client._client = AsyncMock()
        client._client.get.return_value = mock_api_error

        jobs = await client.search_jobs("Developer", "gb")

        assert jobs == []


class TestMultiPageSearch:

    @pytest.mark.asyncio
    async def test_search_all_jobs_basic(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"id": "1", "title": "Job 1"}],
            "count": 1
        }

        client = AdzunaClient("test_id", "test_key", results_per_page=50)
        client._client = AsyncMock()
        client._client.get.return_value = mock_response

        jobs = await client.search_all_jobs("Developer", "gb")

        assert len(jobs) >= 1
        assert jobs[0]["title"] == "Job 1"

    @pytest.mark.asyncio
    async def test_search_all_jobs_empty_results(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [],
            "count": 0
        }

        client = AdzunaClient("test_id", "test_key")
        client._client = AsyncMock()
        client._client.get.return_value = mock_response

        jobs = await client.search_all_jobs("NonexistentJob", "gb")

        assert jobs == []

    @pytest.mark.asyncio
    async def test_search_all_jobs_max_pages_limit(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"id": "1"}],
            "count": 10000
        }

        client = AdzunaClient("test_id", "test_key", results_per_page=10)
        client._client = AsyncMock()
        client._client.get.return_value = mock_response

        await client.search_all_jobs("Developer", "gb", max_pages=3)

        assert client._client.get.call_count <= 3

    @pytest.mark.asyncio
    async def test_search_all_jobs_handles_errors(self):
        mock_response = Mock()
        mock_response.status_code = 500

        client = AdzunaClient("test_id", "test_key")
        client._client = AsyncMock()
        client._client.get.return_value = mock_response

        jobs = await client.search_all_jobs("Developer", "gb")

        assert jobs == []


class TestAPIParameters:

    @pytest.mark.asyncio
    async def test_api_credentials_included(self, mock_api_response):
        client = AdzunaClient("my_id", "my_key")
        client._client = AsyncMock()
        client._client.get.return_value = mock_api_response

        await client.search_jobs("Developer", "gb")

        call_kwargs = client._client.get.call_args[1]
        params = call_kwargs["params"]

        assert params["app_id"] == "my_id"
        assert params["app_key"] == "my_key"

    @pytest.mark.asyncio
    async def test_results_per_page_parameter(self, mock_api_response):
        client = AdzunaClient("test_id", "test_key", results_per_page=25)
        client._client = AsyncMock()
        client._client.get.return_value = mock_api_response

        await client.search_jobs("Developer", "gb")

        call_kwargs = client._client.get.call_args[1]
        params = call_kwargs["params"]

        assert params["results_per_page"] == 25

    @pytest.mark.asyncio
    async def test_what_parameter_encoding(self, mock_api_response):
        client = AdzunaClient("test_id", "test_key")
        client._client = AsyncMock()
        client._client.get.return_value = mock_api_response

        await client.search_jobs("Software Engineer", "gb")

        call_kwargs = client._client.get.call_args[1]
        params = call_kwargs["params"]

        assert params["what"] == "Software Engineer"


class TestClientClose:

    @pytest.mark.asyncio
    async def test_close_calls_aclose(self):
        client = AdzunaClient("test_id", "test_key")
        client._client = AsyncMock()

        await client.close()

        client._client.aclose.assert_called_once()
