import pytest
from collections import Counter
from app.analysis.skill_extractor import SkillExtractor, KNOWN_SKILLS, SKILL_CATEGORIES, _SKILL_TO_CATEGORY


class TestHTMLStripping:

    def test_strip_basic_tags(self):
        text = "<p>Python developer</p>"
        result = SkillExtractor._strip_html(text)
        assert "<p>" not in result
        assert "</p>" not in result
        assert "Python developer" in result

    def test_decode_html_entities(self):
        text = "C++ &amp; Python"
        result = SkillExtractor._strip_html(text)
        assert "&amp;" not in result
        assert "& Python" in result

    def test_collapse_whitespace(self):
        text = "<p>Python</p>  <br/>  <p>SQL</p>"
        result = SkillExtractor._strip_html(text)
        assert "  " not in result

    def test_empty_string(self):
        assert SkillExtractor._strip_html("") == ""

    def test_no_html(self):
        text = "Plain text with no HTML"
        assert SkillExtractor._strip_html(text) == text


class TestSkillNormalization:

    def test_all_caps_preserved(self):
        assert SkillExtractor._normalize_token("SQL") == "SQL"
        assert SkillExtractor._normalize_token("AWS") == "AWS"
        assert SkillExtractor._normalize_token("API") == "API"

    def test_mixed_case_preserved(self):
        assert SkillExtractor._normalize_token("JavaScript") == "JavaScript"
        assert SkillExtractor._normalize_token("TypeScript") == "TypeScript"
        assert SkillExtractor._normalize_token("PostgreSQL") == "PostgreSQL"

    def test_lowercase_capitalized(self):
        assert SkillExtractor._normalize_token("python") == "Python"
        assert SkillExtractor._normalize_token("docker") == "Docker"

    def test_empty_string(self):
        assert SkillExtractor._normalize_token("") == ""
        assert SkillExtractor._normalize_token("  ") == ""


class TestSkillValidation:

    def test_rejects_empty(self):
        assert not SkillExtractor._is_valid_skill("")

    def test_rejects_single_char(self):
        assert not SkillExtractor._is_valid_skill("a")
        assert not SkillExtractor._is_valid_skill("x")

    def test_rejects_pure_numbers(self):
        assert not SkillExtractor._is_valid_skill("123")
        assert not SkillExtractor._is_valid_skill("42")

    def test_accepts_technical_terms(self):
        assert SkillExtractor._is_valid_skill("Python")
        assert SkillExtractor._is_valid_skill("SQL")
        assert SkillExtractor._is_valid_skill("Docker")
        assert SkillExtractor._is_valid_skill("Kubernetes")
        assert SkillExtractor._is_valid_skill("Machine Learning")


class TestSkillExtraction:

    def test_extracts_from_text(self, skill_extractor):
        jobs = [{
            "title": "Python Developer",
            "description": "Experience with SQL, Docker, and Kubernetes required."
        }]
        result = skill_extractor.extract_skills_from_jobs(jobs)
        assert isinstance(result, Counter)
        assert len(result) > 0

    def test_per_job_counting(self, skill_extractor):
        jobs = [
            {"title": "Python Developer", "description": "SQL experience"},
            {"title": "Python Engineer", "description": "AWS and Docker"},
        ]
        result = skill_extractor.extract_skills_from_jobs(jobs)
        assert isinstance(result, Counter)
        assert len(result) > 0

    def test_cross_job_counting(self, skill_extractor):
        jobs = [
            {"title": "Python Developer", "description": "Python and SQL"},
            {"title": "Python Engineer", "description": "Python and AWS"},
            {"title": "Python Analyst", "description": "Python and Docker"},
        ]
        result = skill_extractor.extract_skills_from_jobs(jobs)
        python_count = result.get("Python", 0)
        assert python_count >= 1

    def test_handles_html(self, skill_extractor):
        jobs = [{
            "title": "Developer",
            "description": "<p>Python &amp; SQL experience</p><br/><strong>Docker</strong>"
        }]
        result = skill_extractor.extract_skills_from_jobs(jobs)
        assert isinstance(result, Counter)
        assert len(result) > 0

    def test_empty_input(self, skill_extractor):
        result = skill_extractor.extract_skills_from_jobs([])
        assert isinstance(result, Counter)
        assert len(result) == 0

    def test_missing_fields(self, skill_extractor):
        jobs = [{"id": "1"}]
        result = skill_extractor.extract_skills_from_jobs(jobs)
        assert isinstance(result, Counter)

    def test_returns_counter_type(self, skill_extractor):
        jobs = [{"title": "Test", "description": "Python SQL AWS"}]
        result = skill_extractor.extract_skills_from_jobs(jobs)
        assert isinstance(result, Counter)


class TestKeywordExtraction:

    def test_extracts_known_skills(self, skill_extractor):
        jobs = [{"title": "Developer", "description": "Python and SQL experience"}]
        result = skill_extractor.extract_skills_from_jobs(jobs, country="de")
        assert "Python" in result
        assert "SQL" in result

    def test_word_boundary_matching(self, skill_extractor):
        jobs = [{"title": "Dev", "description": "We use JavaScript daily"}]
        result = skill_extractor.extract_skills_from_jobs(jobs, country="de")
        assert "JavaScript" in result
        assert "Java" not in result

    def test_java_standalone_matches(self, skill_extractor):
        jobs = [{"title": "Dev", "description": "We use Java for backends"}]
        result = skill_extractor.extract_skills_from_jobs(jobs, country="de")
        assert "Java" in result

    def test_case_insensitive(self, skill_extractor):
        for variant in ["python", "PYTHON", "Python"]:
            jobs = [{"title": "Dev", "description": f"Experience with {variant}"}]
            result = skill_extractor.extract_skills_from_jobs(jobs, country="de")
            assert "Python" in result, f"Failed to match variant: {variant}"

    def test_non_english_text(self, skill_extractor):
        jobs = [{
            "title": "Sviluppatore Software",
            "description": (
                "Cerchiamo un sviluppatore con esperienza in Python e SQL. "
                "Conoscenza di Docker e AWS è un vantaggio."
            ),
        }]
        result = skill_extractor.extract_skills_from_jobs(jobs, country="it")
        assert "Python" in result
        assert "SQL" in result
        assert "Docker" in result
        assert "AWS" in result

    def test_known_skills_comprehensive(self):
        for skill in ["AWS", "Docker", "React", "TypeScript", "Kubernetes",
                       "PostgreSQL", "Terraform", "Python", "Java", "SQL"]:
            assert skill in KNOWN_SKILLS, f"{skill} missing from KNOWN_SKILLS"

    def test_csharp_normalization(self, skill_extractor):
        jobs = [{"title": "Dev", "description": "Experience with C # and .NET"}]
        result = skill_extractor.extract_skills_from_jobs(jobs, country="de")
        assert "C#" in result
        assert ".NET" in result


class TestHybridExtraction:

    def test_english_country_uses_both(self, skill_extractor):
        jobs = [{
            "title": "Python Developer",
            "description": "Experience with SQL, Docker, and Kubernetes required."
        }]
        result = skill_extractor.extract_skills_from_jobs(jobs, country="gb")
        assert isinstance(result, Counter)
        assert "Python" in result
        assert "SQL" in result
        assert "Docker" in result

    def test_non_english_country_keyword_only(self, skill_extractor):
        jobs = [{
            "title": "Softwareentwickler",
            "description": (
                "Wir suchen einen Entwickler mit Python und SQL Kenntnissen. "
                "Erfahrung mit Docker ist wünschenswert."
            ),
        }]
        result = skill_extractor.extract_skills_from_jobs(jobs, country="de")
        assert "Python" in result
        assert "SQL" in result
        assert "Docker" in result
        for skill_name in result:
            assert skill_name not in ("Wir", "Entwickler", "Erfahrung", "Kenntnissen")

    def test_country_parameter_default(self, skill_extractor):
        jobs = [{"title": "Python Developer", "description": "SQL and AWS"}]
        result = skill_extractor.extract_skills_from_jobs(jobs)
        assert isinstance(result, Counter)
        assert "Python" in result


class TestSkillCategories:

    def test_all_categorized_skills_in_known_skills(self):
        for category, skills in SKILL_CATEGORIES.items():
            for skill in skills:
                assert skill in KNOWN_SKILLS, f"{skill} in category '{category}' not in KNOWN_SKILLS"

    def test_reverse_lookup_built(self):
        total = sum(len(skills) for skills in SKILL_CATEGORIES.values())
        assert len(_SKILL_TO_CATEGORY) == total

    def test_reverse_lookup_correct(self):
        assert _SKILL_TO_CATEGORY["Python"] == "Languages"
        assert _SKILL_TO_CATEGORY["React"] == "Frameworks"
        assert _SKILL_TO_CATEGORY["PostgreSQL"] == "Databases"
        assert _SKILL_TO_CATEGORY["AWS"] == "Cloud & DevOps"
        assert _SKILL_TO_CATEGORY["TensorFlow"] == "Data & ML"
        assert _SKILL_TO_CATEGORY["Git"] == "Tools"
        assert _SKILL_TO_CATEGORY["CI/CD"] == "Concepts"

    def test_categories_not_empty(self):
        for category, skills in SKILL_CATEGORIES.items():
            assert len(skills) > 0, f"Category '{category}' is empty"
