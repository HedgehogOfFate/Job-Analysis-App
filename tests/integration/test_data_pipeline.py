import pytest
from unittest.mock import patch
from app.analysis.analyzer import JobAnalyzer
from app.exporter.exporter import DataExporter, ChartExporter


class TestFetchAnalyzeExportPipeline:

    def test_full_pipeline_csv_export(self, sample_jobs):
        analyzer = JobAnalyzer()
        result = analyzer.analyze(sample_jobs)

        assert result["total_jobs"] == 3
        assert "London" in result["jobs_by_location"]

        csv_data = DataExporter.to_csv(result)

        assert "Total Jobs,3" in csv_data
        assert "London" in csv_data
        assert "SUMMARY" in csv_data

    def test_full_pipeline_json_export(self, sample_jobs):
        import json

        analyzer = JobAnalyzer()
        result = analyzer.analyze(sample_jobs)

        json_data = DataExporter.to_json(result)
        parsed = json.loads(json_data)

        assert parsed["total_jobs"] == 3
        assert "London" in parsed["jobs_by_location"]

    def test_full_pipeline_excel_export(self, sample_jobs):
        analyzer = JobAnalyzer()
        result = analyzer.analyze(sample_jobs)

        xlsx_data = DataExporter.to_xlsx(result)

        assert isinstance(xlsx_data, bytes)
        assert len(xlsx_data) > 0
        assert xlsx_data[:2] == b'PK'


class TestAnalyzeAndVisualizePipeline:

    def test_analysis_to_location_chart(self, sample_jobs):
        analyzer = JobAnalyzer()
        result = analyzer.analyze(sample_jobs)

        location_chart = ChartExporter.create_location_chart(
            result["jobs_by_location"]
        )

        assert len(location_chart) > 0
        assert location_chart[:8] == b'\x89PNG\r\n\x1a\n'

    def test_analysis_to_skills_chart(self, sample_jobs):
        analyzer = JobAnalyzer()
        result = analyzer.analyze(sample_jobs)

        skills_chart = ChartExporter.create_skills_chart(
            result["top_skills"]
        )

        assert len(skills_chart) > 0
        assert skills_chart[:8] == b'\x89PNG\r\n\x1a\n'

    def test_analysis_to_both_charts(self, sample_jobs):
        analyzer = JobAnalyzer()
        result = analyzer.analyze(sample_jobs)

        location_chart = ChartExporter.create_location_chart(
            result["jobs_by_location"]
        )
        skills_chart = ChartExporter.create_skills_chart(
            result["top_skills"]
        )

        assert location_chart[:8] == b'\x89PNG\r\n\x1a\n'
        assert skills_chart[:8] == b'\x89PNG\r\n\x1a\n'
        assert len(location_chart) > 0
        assert len(skills_chart) > 0


class TestDataTransformationPipeline:

    def test_raw_to_structured_to_export(self, sample_jobs):
        raw_jobs = sample_jobs
        assert isinstance(raw_jobs, list)

        analyzer = JobAnalyzer()
        structured_data = analyzer.analyze(raw_jobs)
        assert isinstance(structured_data, dict)
        assert "total_jobs" in structured_data

        csv_export = DataExporter.to_csv(structured_data)
        json_export = DataExporter.to_json(structured_data)
        xlsx_export = DataExporter.to_xlsx(structured_data)

        assert isinstance(csv_export, str)
        assert isinstance(json_export, str)
        assert isinstance(xlsx_export, bytes)

    def test_locations_pipeline(self, sample_jobs):
        analyzer = JobAnalyzer()
        result = analyzer.analyze(sample_jobs)

        locations = result["jobs_by_location"]
        assert "London" in locations
        assert locations["London"] == 1

        csv_data = DataExporter.to_csv(result)
        assert "London,1" in csv_data

        chart_data = ChartExporter.create_location_chart(locations)
        assert len(chart_data) > 0

    def test_skills_pipeline(self, sample_jobs):
        analyzer = JobAnalyzer()
        result = analyzer.analyze(sample_jobs)

        skills = result["top_skills"]
        assert len(skills) > 0

        csv_data = DataExporter.to_csv(result)
        assert "Skill,Frequency" in csv_data

        chart_data = ChartExporter.create_skills_chart(skills)
        assert len(chart_data) > 0


class TestErrorPropagation:

    def test_empty_jobs_through_pipeline(self):
        analyzer = JobAnalyzer()
        result = analyzer.analyze([])

        assert result["total_jobs"] == 0

        csv_data = DataExporter.to_csv(result)
        json_data = DataExporter.to_json(result)
        xlsx_data = DataExporter.to_xlsx(result)

        assert "Total Jobs,0" in csv_data
        assert isinstance(json_data, str)
        assert isinstance(xlsx_data, bytes)

    def test_malformed_jobs_through_pipeline(self):
        malformed_jobs = [
            {"id": "1"},
            {"id": "2", "title": "Test"}
        ]

        analyzer = JobAnalyzer()
        result = analyzer.analyze(malformed_jobs)

        assert result["total_jobs"] == 2
        assert isinstance(result["jobs_by_location"], dict)


class TestDataConsistency:

    def test_job_count_consistency(self, sample_jobs):
        analyzer = JobAnalyzer()
        result = analyzer.analyze(sample_jobs)

        assert result["total_jobs"] == 3

        csv_data = DataExporter.to_csv(result)
        assert "Total Jobs,3" in csv_data

        import json
        json_data = DataExporter.to_json(result)
        parsed = json.loads(json_data)
        assert parsed["total_jobs"] == 3

    def test_location_count_consistency(self, sample_jobs):
        analyzer = JobAnalyzer()
        result = analyzer.analyze(sample_jobs)

        london_count = result["jobs_by_location"]["London"]

        csv_data = DataExporter.to_csv(result)
        assert f"London,{london_count}" in csv_data

        import json
        json_data = DataExporter.to_json(result)
        parsed = json.loads(json_data)
        assert parsed["jobs_by_location"]["London"] == london_count


class TestCompleteWorkflow:

    def test_search_analyze_export_all_formats(self, sample_jobs):
        analyzer = JobAnalyzer()
        result = analyzer.analyze(sample_jobs)

        csv_data = DataExporter.to_csv(result)
        json_data = DataExporter.to_json(result)
        xlsx_data = DataExporter.to_xlsx(result)
        location_chart = ChartExporter.create_location_chart(result["jobs_by_location"])
        skills_chart = ChartExporter.create_skills_chart(result["top_skills"])

        assert len(csv_data) > 0
        assert len(json_data) > 0
        assert len(xlsx_data) > 0
        assert len(location_chart) > 0
        assert len(skills_chart) > 0

    def test_multiple_searches_sequential(self, sample_jobs):
        analyzer = JobAnalyzer()

        result1 = analyzer.analyze(sample_jobs[:2])
        assert result1["total_jobs"] == 2

        result2 = analyzer.analyze(sample_jobs[1:])
        assert result2["total_jobs"] == 2

        assert result1["total_jobs"] == result2["total_jobs"]
