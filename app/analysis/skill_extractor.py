import re
import html
from collections import Counter
from typing import List, Dict, Any, Set, Tuple

KNOWN_SKILLS: frozenset = frozenset({
    # Programming languages
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust",
    "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "MATLAB", "Perl", "Lua",
    "Haskell", "Erlang", "Elixir", "Clojure", "Dart", "Julia", "Groovy",
    "VBA", "COBOL", "Fortran", "Assembly", "Bash", "PowerShell", "Shell",
    # Web frontend
    "React", "Angular", "Vue.js", "Next.js", "Nuxt.js", "Svelte", "jQuery",
    "Bootstrap", "Tailwind CSS", "HTML", "CSS", "SASS", "LESS", "Webpack",
    "Vite", "REST", "GraphQL", "WebSocket", "OAuth", "JWT",
    # Backend frameworks
    "Node.js", "Express", "Django", "Flask", "FastAPI", "Spring",
    "Spring Boot", ".NET", "ASP.NET", "Laravel", "Rails", "Gin", "Fiber",
    "NestJS", "Actix",
    # Data / ML
    "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "Pandas", "NumPy",
    "SciPy", "Spark", "Hadoop", "Kafka", "Airflow", "dbt", "Snowflake",
    "Databricks", "Tableau", "Power BI", "Looker", "Matplotlib", "Seaborn",
    "NLTK", "spaCy", "Hugging Face", "OpenCV", "MLflow",
    # Databases
    "SQL", "MySQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch",
    "Cassandra", "DynamoDB", "Oracle DB", "SQL Server", "MariaDB", "SQLite",
    "Neo4j", "CouchDB", "InfluxDB",
    # Cloud / DevOps
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "Ansible",
    "Jenkins", "GitHub Actions", "GitLab CI", "CircleCI", "Travis CI",
    "ArgoCD", "Helm", "Prometheus", "Grafana", "Datadog", "New Relic",
    "Splunk", "ELK", "Nginx", "Apache", "Istio", "Consul",
    # Tools
    "Git", "GitHub", "GitLab", "Bitbucket", "Jira", "Confluence", "Slack",
    "VS Code", "IntelliJ", "Figma", "Postman", "Swagger", "OpenAPI",
    # Concepts / practices
    "CI/CD", "DevOps", "MLOps", "DataOps", "Agile", "Scrum", "Kanban",
    "TDD", "BDD", "Microservices", "Serverless", "REST API", "GraphQL API",
    "ETL", "ELT", "Data Warehouse", "Data Lake", "Machine Learning",
    "Deep Learning", "NLP", "Computer Vision", "Reinforcement Learning",
    "Linux", "Unix", "Windows Server", "Networking", "TCP/IP", "DNS",
    "HTTP", "HTTPS", "SSL/TLS", "SAML", "Active Directory", "LDAP",
    # Microsoft / office
    "Excel", "SharePoint", "Outlook",
})

SKILL_CATEGORIES: Dict[str, List[str]] = {
    "Languages": [
        "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust",
        "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "MATLAB", "Perl", "Lua",
        "Haskell", "Erlang", "Elixir", "Clojure", "Dart", "Julia", "Groovy",
        "VBA", "COBOL", "Fortran", "Assembly", "Bash", "PowerShell", "Shell",
    ],
    "Frameworks": [
        "React", "Angular", "Vue.js", "Next.js", "Nuxt.js", "Svelte", "jQuery",
        "Node.js", "Express", "Django", "Flask", "FastAPI", "Spring",
        "Spring Boot", ".NET", "ASP.NET", "Laravel", "Rails", "Gin", "Fiber",
        "NestJS", "Actix",
    ],
    "Databases": [
        "SQL", "MySQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch",
        "Cassandra", "DynamoDB", "Oracle DB", "SQL Server", "MariaDB", "SQLite",
        "Neo4j", "CouchDB", "InfluxDB",
    ],
    "Cloud & DevOps": [
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "Ansible",
        "Jenkins", "GitHub Actions", "GitLab CI", "CircleCI", "Travis CI",
        "ArgoCD", "Helm", "Prometheus", "Grafana", "Datadog", "New Relic",
        "Splunk", "ELK", "Nginx", "Apache", "Istio", "Consul",
    ],
    "Data & ML": [
        "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "Pandas", "NumPy",
        "SciPy", "Spark", "Hadoop", "Kafka", "Airflow", "dbt", "Snowflake",
        "Databricks", "Tableau", "Power BI", "Looker", "Matplotlib", "Seaborn",
        "NLTK", "spaCy", "Hugging Face", "OpenCV", "MLflow",
    ],
    "Tools": [
        "Git", "GitHub", "GitLab", "Bitbucket", "Jira", "Confluence", "Slack",
        "VS Code", "IntelliJ", "Figma", "Postman", "Swagger", "OpenAPI",
    ],
    "Web Frontend": [
        "Bootstrap", "Tailwind CSS", "HTML", "CSS", "SASS", "LESS", "Webpack",
        "Vite", "REST", "GraphQL", "WebSocket", "OAuth", "JWT",
    ],
    "Concepts": [
        "CI/CD", "DevOps", "MLOps", "DataOps", "Agile", "Scrum", "Kanban",
        "TDD", "BDD", "Microservices", "Serverless", "REST API", "GraphQL API",
        "ETL", "ELT", "Data Warehouse", "Data Lake", "Machine Learning",
        "Deep Learning", "NLP", "Computer Vision", "Reinforcement Learning",
        "Linux", "Unix", "Windows Server", "Networking", "TCP/IP", "DNS",
        "HTTP", "HTTPS", "SSL/TLS", "SAML", "Active Directory", "LDAP",
        "Excel", "SharePoint", "Outlook",
    ],
}

_SKILL_TO_CATEGORY: Dict[str, str] = {}
for _cat, _skills in SKILL_CATEGORIES.items():
    for _skill in _skills:
        _SKILL_TO_CATEGORY[_skill] = _cat

_HTML_TAG_RE = re.compile(r"<[^>]+>")


class SkillExtractor:

    def __init__(self):
        self._keyword_patterns: Dict[str, Tuple[str, "re.Pattern[str]"]] = {}
        for skill in KNOWN_SKILLS:
            key = skill.lower()
            escaped = re.escape(skill)
            pattern = re.compile(
                r"(?<!\w)" + escaped + r"(?!\w)", re.IGNORECASE
            )
            self._keyword_patterns[key] = (skill, pattern)

    def extract_skills_from_jobs(
        self, jobs: List[Dict[str, Any]], country: str = "gb"
    ) -> Counter:
        counter: Counter = Counter()
        for job in jobs:
            title = job.get("title") or ""
            desc = job.get("description") or ""
            raw = f"{title}. {desc}"
            text = self._strip_html(raw)
            for skill in self._keyword_extract(text):
                counter[skill] += 1
        return counter

    def _keyword_extract(self, text: str) -> Set[str]:
        found: Set[str] = set()
        for _key, (display_name, pattern) in self._keyword_patterns.items():
            if pattern.search(text):
                found.add(display_name)
        return found

    @staticmethod
    def _strip_html(text: str) -> str:
        text = _HTML_TAG_RE.sub(" ", text)
        text = html.unescape(text)
        text = re.sub(r"\bC\s+#", "C#", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def _normalize_token(text: str) -> str:
        stripped = text.strip()
        if not stripped:
            return stripped
        if stripped.isupper():
            return stripped
        if not stripped.islower():
            return stripped
        return stripped.capitalize()

    @staticmethod
    def _is_valid_skill(text: str) -> bool:
        if not text or len(text) <= 1:
            return False
        if text.isdigit():
            return False
        return True
