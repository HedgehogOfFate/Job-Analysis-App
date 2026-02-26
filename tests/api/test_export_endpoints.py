import pytest
from unittest.mock import patch


class TestCSVExportEndpoint:

    def test_export_csv_success(self, test_client, sample_analysis_result):
        with patch('app.main.last_search_result', sample_analysis_result):
            response = test_client.get("/api/export/csv")

            assert response.status_code == 200
            assert response.headers["content-type"] == "text/csv; charset=utf-8"
            assert "attachment" in response.headers["content-disposition"]
            assert "job_analysis.csv" in response.headers["content-disposition"]

    def test_export_csv_content(self, test_client, sample_analysis_result):
        with patch('app.main.last_search_result', sample_analysis_result):
            response = test_client.get("/api/export/csv")

            assert response.status_code == 200
            content = response.text
            assert "Total Jobs,150" in content
            assert "SUMMARY" in content
            assert "JOBS BY LOCATION" in content

    def test_export_csv_without_search(self, test_client):
        with patch('app.main.last_search_result', {}):
            response = test_client.get("/api/export/csv")

            assert response.status_code == 400
            error = response.json()
            assert "No search results available" in error["detail"]


class TestJSONExportEndpoint:
    def test_export_json_success(self, test_client, sample_analysis_result):
        with patch('app.main.last_search_result', sample_analysis_result):
            response = test_client.get("/api/export/json")

            assert response.status_code == 200
            assert "application/json" in response.headers["content-type"]
            assert "attachment" in response.headers["content-disposition"]
            assert "job_analysis.json" in response.headers["content-disposition"]

    def test_export_json_content(self, test_client, sample_analysis_result):
        with patch('app.main.last_search_result', sample_analysis_result):
            response = test_client.get("/api/export/json")

            assert response.status_code == 200
            data = response.json()
            assert data["total_jobs"] == 150
            assert "jobs_by_location" in data
            assert "top_skills" in data

    def test_export_json_without_search(self, test_client):
        with patch('app.main.last_search_result', {}):
            response = test_client.get("/api/export/json")

            assert response.status_code == 400


class TestExcelExportEndpoint:

    def test_export_xlsx_success(self, test_client, sample_analysis_result):
        with patch('app.main.last_search_result', sample_analysis_result):
            response = test_client.get("/api/export/xlsx")

            assert response.status_code == 200
            assert "spreadsheetml.sheet" in response.headers["content-type"]
            assert "attachment" in response.headers["content-disposition"]
            assert "job_analysis.xlsx" in response.headers["content-disposition"]

    def test_export_xlsx_content(self, test_client, sample_analysis_result):
        with patch('app.main.last_search_result', sample_analysis_result):
            response = test_client.get("/api/export/xlsx")

            assert response.status_code == 200
            assert response.content[:2] == b'PK'
            assert len(response.content) > 0

    def test_export_xlsx_without_search(self, test_client):
        with patch('app.main.last_search_result', {}):
            response = test_client.get("/api/export/xlsx")

            assert response.status_code == 400


class TestLocationChartExportEndpoint:

    def test_export_location_chart_success(self, test_client, sample_analysis_result):
        with patch('app.main.last_search_result', sample_analysis_result):
            response = test_client.get("/api/export/chart/location")

            assert response.status_code == 200
            assert response.headers["content-type"] == "image/png"
            assert "attachment" in response.headers["content-disposition"]
            assert "location_chart.png" in response.headers["content-disposition"]

    def test_export_location_chart_content(self, test_client, sample_analysis_result):
        with patch('app.main.last_search_result', sample_analysis_result):
            response = test_client.get("/api/export/chart/location")

            assert response.status_code == 200
            assert response.content[:8] == b'\x89PNG\r\n\x1a\n'
            assert len(response.content) > 0

    def test_export_location_chart_without_search(self, test_client):
        with patch('app.main.last_search_result', {}):
            response = test_client.get("/api/export/chart/location")

            assert response.status_code == 400

    def test_export_location_chart_empty_data(self, test_client):
        empty_result = {
            "total_jobs": 0,
            "jobs_by_location": {},
            "top_skills": [],
            "salary_stats": {"count": 0}
        }
        with patch('app.main.last_search_result', empty_result):
            response = test_client.get("/api/export/chart/location")

            assert response.status_code in [200, 400]


class TestSkillsChartExportEndpoint:

    def test_export_skills_chart_success(self, test_client, sample_analysis_result):
        with patch('app.main.last_search_result', sample_analysis_result):
            response = test_client.get("/api/export/chart/skills")

            assert response.status_code == 200
            assert response.headers["content-type"] == "image/png"
            assert "attachment" in response.headers["content-disposition"]
            assert "skills_chart.png" in response.headers["content-disposition"]

    def test_export_skills_chart_content(self, test_client, sample_analysis_result):
        with patch('app.main.last_search_result', sample_analysis_result):
            response = test_client.get("/api/export/chart/skills")

            assert response.status_code == 200
            assert response.content[:8] == b'\x89PNG\r\n\x1a\n'
            assert len(response.content) > 0

    def test_export_skills_chart_without_search(self, test_client):
        with patch('app.main.last_search_result', {}):
            response = test_client.get("/api/export/chart/skills")

            assert response.status_code == 400


class TestExportWorkflow:

    @patch('app.main.adzuna.search_all_jobs')
    def test_search_then_export_all_formats(self, mock_search, test_client, sample_jobs):
        mock_search.return_value = sample_jobs

        search_response = test_client.get(
            "/api/search?what=Developer&country=gb"
        )
        assert search_response.status_code == 200

        csv_response = test_client.get("/api/export/csv")
        assert csv_response.status_code == 200

        json_response = test_client.get("/api/export/json")
        assert json_response.status_code == 200

        xlsx_response = test_client.get("/api/export/xlsx")
        assert xlsx_response.status_code == 200

        location_response = test_client.get("/api/export/chart/location")
        assert location_response.status_code == 200

        skills_response = test_client.get("/api/export/chart/skills")
        assert skills_response.status_code == 200


class TestExportContentHeaders:

    def test_csv_download_headers(self, test_client, sample_analysis_result):
        with patch('app.main.last_search_result', sample_analysis_result):
            response = test_client.get("/api/export/csv")

            assert "text/csv" in response.headers["content-type"]
            assert "attachment" in response.headers["content-disposition"]
            assert "filename=" in response.headers["content-disposition"]

    def test_json_download_headers(self, test_client, sample_analysis_result):
        with patch('app.main.last_search_result', sample_analysis_result):
            response = test_client.get("/api/export/json")

            assert "application/json" in response.headers["content-type"]
            assert "attachment" in response.headers["content-disposition"]

    def test_xlsx_download_headers(self, test_client, sample_analysis_result):
        with patch('app.main.last_search_result', sample_analysis_result):
            response = test_client.get("/api/export/xlsx")

            assert "spreadsheetml.sheet" in response.headers["content-type"]
            assert "attachment" in response.headers["content-disposition"]

    def test_chart_download_headers(self, test_client, sample_analysis_result):
        with patch('app.main.last_search_result', sample_analysis_result):
            location_response = test_client.get("/api/export/chart/location")
            skills_response = test_client.get("/api/export/chart/skills")

            assert location_response.headers["content-type"] == "image/png"
            assert skills_response.headers["content-type"] == "image/png"
            assert "attachment" in location_response.headers["content-disposition"]
            assert "attachment" in skills_response.headers["content-disposition"]


class TestExportFileSize:

    def test_csv_file_size(self, test_client, sample_analysis_result):
        with patch('app.main.last_search_result', sample_analysis_result):
            response = test_client.get("/api/export/csv")

            assert len(response.content) > 100
            assert len(response.content) < 1000000

    def test_json_file_size(self, test_client, sample_analysis_result):
        with patch('app.main.last_search_result', sample_analysis_result):
            response = test_client.get("/api/export/json")

            assert len(response.content) > 100
            assert len(response.content) < 1000000

    def test_chart_file_size(self, test_client, sample_analysis_result):
        with patch('app.main.last_search_result', sample_analysis_result):
            location_response = test_client.get("/api/export/chart/location")
            skills_response = test_client.get("/api/export/chart/skills")

            assert 10000 < len(location_response.content) < 5000000
            assert 10000 < len(skills_response.content) < 5000000