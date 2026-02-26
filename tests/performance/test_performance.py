import pytest
import time
import asyncio
from unittest.mock import patch, Mock, AsyncMock


class TestAnalysisPerformance:

    def test_large_dataset_analysis_speed(self, large_job_dataset, job_analyzer):
        start_time = time.time()
        result = job_analyzer.analyze(large_job_dataset)
        duration = time.time() - start_time

        assert duration < 30.0, f"Analysis took {duration:.2f}s, required < 30s"

        assert result["total_jobs"] == 500
        assert len(result["jobs_by_location"]) > 0
        assert len(result["top_skills"]) > 0

    def test_medium_dataset_performance(self, job_analyzer):
        jobs = []
        for i in range(100):
            jobs.append({
                "id": str(i),
                "title": f"Job {i}",
                "description": "Experience with Python, SQL, and AWS required.",
                "location": {"area": ["London"], "display_name": "London"},
                "salary_min": 50000,
                "salary_max": 70000,
                "salary_is_predicted": False
            })

        start_time = time.time()
        result = job_analyzer.analyze(jobs)
        duration = time.time() - start_time

        assert duration < 15.0, f"100 jobs took {duration:.2f}s"
        assert result["total_jobs"] == 100

    def test_small_dataset_performance(self, job_analyzer, sample_jobs):
        start_time = time.time()
        result = job_analyzer.analyze(sample_jobs)
        duration = time.time() - start_time

        assert duration < 2.0, f"3 jobs took {duration:.2f}s"
        assert result["total_jobs"] == 3


class TestExportPerformance:

    def test_csv_export_speed(self, sample_analysis_result):
        from app.exporter.exporter import DataExporter

        start_time = time.time()
        csv_data = DataExporter.to_csv(sample_analysis_result)
        duration = time.time() - start_time

        assert duration < 1.0, f"CSV export took {duration:.2f}s"
        assert len(csv_data) > 0

    def test_json_export_speed(self, sample_analysis_result):
        from app.exporter.exporter import DataExporter

        start_time = time.time()
        json_data = DataExporter.to_json(sample_analysis_result)
        duration = time.time() - start_time

        assert duration < 1.0, f"JSON export took {duration:.2f}s"
        assert len(json_data) > 0

    def test_excel_export_speed(self, sample_analysis_result):
        from app.exporter.exporter import DataExporter

        start_time = time.time()
        xlsx_data = DataExporter.to_xlsx(sample_analysis_result)
        duration = time.time() - start_time

        assert duration < 1.0, f"Excel export took {duration:.2f}s"
        assert len(xlsx_data) > 0

    def test_all_exports_combined_speed(self, sample_analysis_result):
        from app.exporter.exporter import DataExporter

        start_time = time.time()

        csv_data = DataExporter.to_csv(sample_analysis_result)
        json_data = DataExporter.to_json(sample_analysis_result)
        xlsx_data = DataExporter.to_xlsx(sample_analysis_result)

        duration = time.time() - start_time

        assert duration < 3.0, f"All exports took {duration:.2f}s"


class TestChartPerformance:

    def test_location_chart_generation_speed(self):
        from app.exporter.exporter import ChartExporter

        location_data = {f"City{i}": i * 10 for i in range(50)}

        start_time = time.time()
        chart = ChartExporter.create_location_chart(location_data)
        duration = time.time() - start_time

        assert duration < 2.0, f"Location chart took {duration:.2f}s"
        assert len(chart) > 0

    def test_skills_chart_generation_speed(self):
        from app.exporter.exporter import ChartExporter

        skills_data = [[f"Skill{i}", i * 5] for i in range(20)]

        start_time = time.time()
        chart = ChartExporter.create_skills_chart(skills_data)
        duration = time.time() - start_time

        assert duration < 2.0, f"Skills chart took {duration:.2f}s"
        assert len(chart) > 0

    def test_both_charts_generation_speed(self):
        from app.exporter.exporter import ChartExporter

        location_data = {"London": 100, "Manchester": 50}
        skills_data = [["Python", 80], ["SQL", 65]]

        start_time = time.time()

        location_chart = ChartExporter.create_location_chart(location_data)
        skills_chart = ChartExporter.create_skills_chart(skills_data)

        duration = time.time() - start_time

        assert duration < 4.0, f"Both charts took {duration:.2f}s"


class TestAPIResponseTime:

    @patch('app.main.adzuna.search_all_jobs')
    def test_search_endpoint_response_time(self, mock_search, test_client, sample_jobs):
        mock_search.return_value = sample_jobs

        start_time = time.time()
        response = test_client.get(
            "/api/search?what=Developer&country=gb"
        )
        duration = time.time() - start_time

        assert response.status_code == 200
        assert duration < 1.0, f"Search endpoint took {duration:.2f}s"

    def test_export_endpoint_response_time(self, test_client, sample_analysis_result):
        with patch('app.main.last_search_result', sample_analysis_result):
            start = time.time()
            csv_response = test_client.get("/api/export/csv")
            csv_time = time.time() - start

            start = time.time()
            json_response = test_client.get("/api/export/json")
            json_time = time.time() - start

            assert csv_response.status_code == 200
            assert json_response.status_code == 200
            assert csv_time < 1.0
            assert json_time < 1.0


class TestConcurrentRequests:

    @pytest.mark.asyncio
    async def test_concurrent_api_calls(self, adzuna_client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"id": "1", "title": "Job"}],
            "count": 1
        }
        adzuna_client._client = AsyncMock()
        adzuna_client._client.get.return_value = mock_response

        start_time = time.time()

        tasks = [
            adzuna_client.search_jobs(f"Job{i}", "gb")
            for i in range(10)
        ]
        results = await asyncio.gather(*tasks)

        duration = time.time() - start_time

        assert duration < 5.0, f"10 concurrent calls took {duration:.2f}s"
        assert len(results) == 10

    @pytest.mark.asyncio
    async def test_sequential_vs_concurrent_performance(self, adzuna_client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"id": "1"}],
            "count": 1
        }
        adzuna_client._client = AsyncMock()
        adzuna_client._client.get.return_value = mock_response

        start = time.time()
        for i in range(5):
            await adzuna_client.search_jobs(f"Job{i}", "gb")
        sequential_time = time.time() - start

        start = time.time()
        tasks = [
            adzuna_client.search_jobs(f"Job{i}", "gb")
            for i in range(5)
        ]
        await asyncio.gather(*tasks)
        concurrent_time = time.time() - start

        assert sequential_time < 1.0
        assert concurrent_time < 1.0


class TestMemoryUsage:

    def test_large_dataset_memory_handling(self, job_analyzer, large_job_dataset):
        result = job_analyzer.analyze(large_job_dataset)

        assert result["total_jobs"] == 500

    def test_multiple_analyses_memory(self, job_analyzer, sample_jobs):

        for _ in range(100):
            result = job_analyzer.analyze(sample_jobs)
            assert result["total_jobs"] == 3


class TestScalability:

    def test_linear_scaling_with_data_size(self, job_analyzer):
        sizes_and_times = []

        for size in [10, 50, 100, 200]:
            jobs = []
            for i in range(size):
                jobs.append({
                    "id": str(i),
                    "title": f"Job {i}",
                    "description": "Experience with Python and SQL required.",
                    "location": {"area": ["London"], "display_name": "London"},
                    "salary_min": 50000,
                    "salary_max": 70000,
                    "salary_is_predicted": False
                })

            start = time.time()
            job_analyzer.analyze(jobs)
            duration = time.time() - start

            sizes_and_times.append((size, duration))

        for i in range(len(sizes_and_times) - 1):
            size1, time1 = sizes_and_times[i]
            size2, time2 = sizes_and_times[i + 1]

            ratio = time2 / time1 if time1 > 0 else 1
            assert ratio < 8.0

    def test_handles_maximum_expected_load(self, job_analyzer):

        jobs = []
        for i in range(1000):
            jobs.append({
                "id": str(i),
                "title": f"Job {i}",
                "description": "Experience with Python, SQL, and AWS required.",
                "location": {"area": [f"City{i % 50}"], "display_name": f"City{i % 50}"},
                "salary_min": 40000 + (i * 10),
                "salary_max": 60000 + (i * 10),
                "salary_is_predicted": False
            })

        start_time = time.time()
        result = job_analyzer.analyze(jobs)
        duration = time.time() - start_time

        assert duration < 60.0, f"1000 jobs took {duration:.2f}s"
        assert result["total_jobs"] == 1000


class TestPerformanceBenchmarks:

    def test_benchmark_analysis_speeds(self, job_analyzer):
        benchmarks = {}

        for size in [10, 50, 100, 500]:
            jobs = []
            for i in range(size):
                jobs.append({
                    "id": str(i),
                    "title": f"Job {i}",
                    "description": "Experience with Python, SQL, AWS, and Docker required.",
                    "location": {"area": ["London"], "display_name": "London"},
                    "salary_min": 50000,
                    "salary_max": 70000,
                    "salary_is_predicted": False
                })

            start = time.time()
            job_analyzer.analyze(jobs)
            duration = time.time() - start

            benchmarks[size] = duration

        print("\n=== Performance Benchmarks ===")
        for size, duration in benchmarks.items():
            print(f"{size} jobs: {duration:.4f}s ({size / duration:.0f} jobs/sec)")

        assert all(d < 60.0 for d in benchmarks.values())