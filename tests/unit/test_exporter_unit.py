import pytest
import json
from app.exporter.exporter import DataExporter, ChartExporter


class TestCSVExport:

    def test_csv_export_structure(self, sample_analysis_result):
        csv_data = DataExporter.to_csv(sample_analysis_result)

        assert "SUMMARY" in csv_data
        assert "JOBS BY LOCATION" in csv_data
        assert "TOP SKILLS" in csv_data

    def test_csv_export_summary_section(self, sample_analysis_result):
        csv_data = DataExporter.to_csv(sample_analysis_result)

        assert "Total Jobs,150" in csv_data
        assert "Average Salary" in csv_data
        assert "Min Salary" in csv_data
        assert "Max Salary" in csv_data

    def test_csv_export_location_section(self, sample_analysis_result):
        csv_data = DataExporter.to_csv(sample_analysis_result)

        assert "Location,Count" in csv_data
        assert "London,100" in csv_data
        assert "Manchester,30" in csv_data

    def test_csv_export_skills_section(self, sample_analysis_result):
        csv_data = DataExporter.to_csv(sample_analysis_result)

        assert "Skill,Frequency" in csv_data
        assert "Python,80" in csv_data
        assert "SQL,65" in csv_data

    def test_csv_export_no_salary_data(self):
        data = {
            "total_jobs": 50,
            "salary_stats": {"count": 0},
            "jobs_by_location": {"London": 50},
            "top_skills": [["Python", 10]]
        }
        csv_data = DataExporter.to_csv(data)

        assert "Total Jobs,50" in csv_data
        assert "Average Salary" not in csv_data


class TestJSONExport:

    def test_json_export_structure(self, sample_analysis_result):
        json_data = DataExporter.to_json(sample_analysis_result)
        parsed = json.loads(json_data)

        assert "total_jobs" in parsed
        assert "jobs_by_location" in parsed
        assert "top_skills" in parsed
        assert "salary_stats" in parsed

    def test_json_export_values(self, sample_analysis_result):
        json_data = DataExporter.to_json(sample_analysis_result)
        parsed = json.loads(json_data)

        assert parsed["total_jobs"] == 150
        assert parsed["jobs_by_location"]["London"] == 100
        assert parsed["top_skills"][0] == ["Python", 80]
        assert parsed["salary_stats"]["avg"] == 55000.0

    def test_json_export_formatting(self, sample_analysis_result):
        json_data = DataExporter.to_json(sample_analysis_result)

        assert "\n" in json_data
        assert "  " in json_data

    def test_json_export_valid(self, sample_analysis_result):
        json_data = DataExporter.to_json(sample_analysis_result)

        parsed = json.loads(json_data)
        assert isinstance(parsed, dict)


class TestExcelExport:

    def test_xlsx_export_generates_bytes(self, sample_analysis_result):
        xlsx_data = DataExporter.to_xlsx(sample_analysis_result)

        assert isinstance(xlsx_data, bytes)
        assert len(xlsx_data) > 0

    def test_xlsx_export_file_header(self, sample_analysis_result):
        xlsx_data = DataExporter.to_xlsx(sample_analysis_result)

        assert xlsx_data[:2] == b'PK'

    def test_xlsx_export_minimum_size(self, sample_analysis_result):
        xlsx_data = DataExporter.to_xlsx(sample_analysis_result)

        assert len(xlsx_data) > 5000

    def test_xlsx_export_empty_data(self):
        data = {
            "total_jobs": 0,
            "salary_stats": {"count": 0},
            "jobs_by_location": {},
            "top_skills": []
        }
        xlsx_data = DataExporter.to_xlsx(data)

        assert isinstance(xlsx_data, bytes)
        assert len(xlsx_data) > 0


class TestLocationChartExport:

    def test_location_chart_basic_generation(self):
        location_data = {
            "London": 100,
            "Manchester": 50,
            "Birmingham": 30
        }

        chart_bytes = ChartExporter.create_location_chart(location_data)

        assert isinstance(chart_bytes, bytes)
        assert len(chart_bytes) > 0

    def test_location_chart_png_format(self):
        location_data = {"London": 100, "Manchester": 50}
        chart_bytes = ChartExporter.create_location_chart(location_data)

        assert chart_bytes[:8] == b'\x89PNG\r\n\x1a\n'

    def test_location_chart_empty_data(self):
        chart_bytes = ChartExporter.create_location_chart({})

        assert isinstance(chart_bytes, bytes)
        assert len(chart_bytes) > 0
        assert chart_bytes[:8] == b'\x89PNG\r\n\x1a\n'

    def test_location_chart_many_locations(self):
        location_data = {f"City{i}": i * 10 for i in range(50)}
        chart_bytes = ChartExporter.create_location_chart(location_data)

        assert isinstance(chart_bytes, bytes)
        assert len(chart_bytes) > 0

    def test_location_chart_single_location(self):
        location_data = {"London": 100}
        chart_bytes = ChartExporter.create_location_chart(location_data)

        assert isinstance(chart_bytes, bytes)
        assert len(chart_bytes) > 0


class TestSkillsChartExport:

    def test_skills_chart_basic_generation(self):
        skills_data = [
            ["Python", 80],
            ["SQL", 65],
            ["AWS", 45]
        ]

        chart_bytes = ChartExporter.create_skills_chart(skills_data)

        assert isinstance(chart_bytes, bytes)
        assert len(chart_bytes) > 0

    def test_skills_chart_png_format(self):
        skills_data = [["Python", 80], ["SQL", 65]]
        chart_bytes = ChartExporter.create_skills_chart(skills_data)

        assert chart_bytes[:8] == b'\x89PNG\r\n\x1a\n'

    def test_skills_chart_top_15_only(self):
        skills_data = [[f"Skill{i}", i * 5] for i in range(30)]
        chart_bytes = ChartExporter.create_skills_chart(skills_data)

        assert isinstance(chart_bytes, bytes)
        assert len(chart_bytes) > 0

    def test_skills_chart_single_skill(self):
        skills_data = [["Python", 100]]
        chart_bytes = ChartExporter.create_skills_chart(skills_data)

        assert isinstance(chart_bytes, bytes)
        assert len(chart_bytes) > 0


class TestChartQuality:

    def test_chart_minimum_size(self):
        location_data = {"London": 100}
        skills_data = [["Python", 80]]

        location_chart = ChartExporter.create_location_chart(location_data)
        skills_chart = ChartExporter.create_skills_chart(skills_data)

        assert len(location_chart) > 10000
        assert len(skills_chart) > 10000

    def test_chart_not_empty(self):
        location_data = {"London": 100, "Manchester": 50}
        skills_data = [["Python", 80], ["SQL", 65]]

        location_chart = ChartExporter.create_location_chart(location_data)
        skills_chart = ChartExporter.create_skills_chart(skills_data)

        assert len(location_chart) > 50000
        assert len(skills_chart) > 50000