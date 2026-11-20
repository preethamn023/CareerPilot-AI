"""Deterministic rule-based analysis used when no AI provider is configured.

Everything here is real, explainable logic - no fake AI output. Results are
clearly labelled `extraction_method: "rule_based"` and the UI shows that the
app is running in offline mode.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher

from app.schemas.analysis import (
    MatchResult,
    MissingSkill,
    PartiallyMatchedSkill,
    ScoreDimension,
    SkillGapItem,
)
from app.schemas.interview import InterviewQuestion
from app.schemas.job import JobDescriptionInfo
from app.schemas.optimization import BulletOptimization
from app.schemas.resume import Education, ExperienceItem, Project, ResumeProfile
from app.config import settings

# --------------------------------------------------------------------------
# Skill dictionary: canonical name -> aliases
# --------------------------------------------------------------------------
SKILL_ALIASES: dict[str, list[str]] = {
    "Python": ["python3", "py"],
    "Java": ["core java", "advanced java", "java 8", "java 17"],
    "JavaScript": ["js", "es6", "ecmascript", "vanilla js"],
    "TypeScript": ["ts"],
    "C": [],
    "C++": ["cpp", "c plus plus"],
    "C#": ["csharp", "c sharp", ".net core", "dotnet", "asp.net"],
    "Go": ["golang"],
    "Rust": [],
    "PHP": [],
    "Kotlin": [],
    "Swift": [],
    "Ruby": ["ruby on rails", "rails"],
    "Dart": [],
    "SQL": ["mysql", "postgresql", "postgres", "sqlite", "oracle sql", "t-sql", "pl/sql", "sql server"],
    "NoSQL": ["mongodb", "mongo", "cassandra", "dynamodb", "couchdb"],
    "Redis": [],
    "HTML": ["html5"],
    "CSS": ["css3"],
    "Tailwind CSS": ["tailwind", "tailwindcss"],
    "Bootstrap": [],
    "React": ["react.js", "reactjs", "react js"],
    "Next.js": ["nextjs", "next js"],
    "Angular": ["angularjs"],
    "Vue.js": ["vue", "vuejs", "vue js"],
    "Node.js": ["nodejs", "node js", "node"],
    "Express": ["express.js", "expressjs", "express js"],
    "NestJS": ["nest.js"],
    "Django": [],
    "Flask": [],
    "FastAPI": ["fast api"],
    "Spring Boot": ["spring", "springboot", "spring-boot"],
    "GraphQL": [],
    "REST API": ["rest", "restful", "rest apis", "web services", "restful api", "restful apis", "api development", "api development"],
    "Microservices": ["micro services", "micro-services"],
    "Docker": ["containerization", "containers"],
    "Kubernetes": ["k8s"],
    "CI/CD": ["ci cd", "cicd", "continuous integration", "continuous delivery", "github actions", "gitlab ci", "jenkins"],
    "Jenkins": [],
    "Terraform": ["iac", "infrastructure as code"],
    "Ansible": [],
    "AWS": ["amazon web services", "ec2", "s3", "lambda", "aws cloud"],
    "Azure": ["microsoft azure"],
    "GCP": ["google cloud", "google cloud platform"],
    "Linux": ["unix", "bash", "shell scripting", "ubuntu"],
    "Git": ["github", "gitlab", "version control", "bitbucket"],
    "Machine Learning": ["ml", "scikit-learn", "sklearn"],
    "Deep Learning": ["neural networks", "cnn", "rnn", "lstm"],
    "NLP": ["natural language processing"],
    "Computer Vision": ["opencv", "image processing"],
    "Data Science": ["data analytics", "analytics"],
    "Data Structures": ["dsa", "data structures and algorithms"],
    "Algorithms": ["algorithm design"],
    "Pandas": [],
    "NumPy": [],
    "TensorFlow": [],
    "PyTorch": [],
    "Power BI": ["powerbi"],
    "Tableau": [],
    "Excel": ["advanced excel", "spreadsheet"],
    "Hadoop": [],
    "Spark": ["pyspark", "apache spark"],
    "Kafka": ["apache kafka"],
    "Elasticsearch": [],
    "Selenium": ["selenium webdriver"],
    "Playwright": [],
    "Cypress": [],
    "pytest": ["py test"],
    "JUnit": ["junit5"],
    "Jira": [],
    "Agile": ["scrum", "kanban", "agile methodologies", "sprint planning"],
    "OOP": ["object oriented programming", "object-oriented programming", "oops"],
    "DBMS": ["database management", "database management system", "database design"],
    "Operating Systems": ["os fundamentals"],
    "Computer Networks": ["networking", "computer network"],
    "Firebase": [],
    "MongoDB": ["mongo db"],
    "Figma": ["ui design", "ux design", "ui ux design", "ui/ux"],
    "Android": ["android development", "android studio"],
    "Flutter": [],
    "iOS": ["ios development"],
    "System Design": ["hld", "lld", "high level design", "low level design"],
    "Communication": ["communication skills", "verbal communication", "written communication", "soft skills", "presentation skills"],
    "Teamwork": ["team work", "collaboration", "team collaboration", "team player"],
    "Leadership": ["team leadership", "leading a team"],
    "Problem Solving": ["problem-solving", "problem solving skills", "analytical skills", "analytical thinking"],
    "Time Management": [],
    "Critical Thinking": [],
    "Research": ["research skills"],
}

# Reverse map alias -> canonical (lowercased)
_ALIAS_TO_CANONICAL: dict[str, str] = {}
for _canon, _aliases in SKILL_ALIASES.items():
    _ALIAS_TO_CANONICAL[_canon.lower()] = _canon
    for _alias in _aliases:
        _ALIAS_TO_CANONICAL[_alias.lower()] = _canon

ALL_SKILL_NAMES = sorted(_ALIAS_TO_CANONICAL.keys())


def normalize_skill(name: str) -> str | None:
    """Normalise a skill string to its canonical dictionary name."""
    if not name:
        return None
    key = re.sub(r"\s+", " ", name.strip().lower())
    if key in _ALIAS_TO_CANONICAL:
        return _ALIAS_TO_CANONICAL[key]
    # try singular/plural and symbol variants
    for variant in (key.rstrip("s"), key.replace(".", "").replace("-", " ")):
        if variant in _ALIAS_TO_CANONICAL:
            return _ALIAS_TO_CANONICAL[variant]
    return None


def fuzzy_find_skill(text: str, threshold: float = 0.86) -> list[str]:
    """Find dictionary skills mentioned in free text (word-boundary aware).
    Returns canonical names."""
    found: list[str] = []
    text_lower = " " + re.sub(r"\s+", " ", text.lower()) + " "
    for alias, canonical in _ALIAS_TO_CANONICAL.items():
        if len(alias) < 2:
            continue
        pattern = r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])"
        if re.search(pattern, text_lower):
            if canonical not in found:
                found.append(canonical)
    # Fuzzy pass for typos (only for aliases of length >= 5). A word that
    # merely CONTAINS the alias (e.g. "javascripting") is a different term,
    # not a typo - skip it.
    words = set(re.findall(r"[a-z][a-z+#.\-]{3,}", text_lower))
    for alias, canonical in _ALIAS_TO_CANONICAL.items():
        if len(alias) < 5 or canonical in found:
            continue
        for word in words:
            if alias in word or word in alias:
                continue
            if abs(len(word) - len(alias)) <= 3 and SequenceMatcher(None, alias, word).ratio() >= 0.86:
                found.append(canonical)
                break
    return found


# --------------------------------------------------------------------------
# Resume section splitting
# --------------------------------------------------------------------------
SECTION_HEADERS = {
    "summary": ["summary", "professional summary", "objective", "career objective", "profile", "about me", "professional profile"],
    "education": ["education", "academics", "educational qualification", "educational qualifications", "academic background"],
    "skills": ["technical skills", "skills", "skill set", "technologies", "technical proficiencies", "it skills", "computer skills"],
    "projects": ["projects", "academic projects", "personal projects", "key projects", "project work"],
    "internships": ["internships", "internship", "internship experience", "industrial training"],
    "experience": ["work experience", "experience", "professional experience", "employment history", "work history"],
    "certifications": ["certifications", "certificates", "certification courses", "licenses"],
    "achievements": ["achievements", "awards", "honors", "honours", "extra-curricular", "extracurricular activities", "positions of responsibility"],
}

_DEGREE_PATTERNS = [
    r"b\.?\s?tech", r"b\.?e\b", r"b\.?sc", r"m\.?\s?tech", r"m\.?\s?sc", r"mca\b",
    r"bca\b", r"bachelor", r"master", r"ph\.?d", r"diploma", r"mba", r"b\.?com", r"m\.?com",
]
_EDUCATION_LINE_RE = re.compile("|".join(_DEGREE_PATTERNS), re.IGNORECASE)
_INSTITUTION_RE = re.compile(r"(college|university|institute|school|academy|campus|polytechnic)\b", re.IGNORECASE)
_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
_CGPA_RE = re.compile(r"\b(cgpa|gpa|percentage)\b[:\s]*([0-9.]+)", re.IGNORECASE)


def split_sections(text: str) -> dict[str, list[str]]:
    """Split raw resume text into sections based on common heading names."""
    lines = [line.strip() for line in text.splitlines()]
    sections: dict[str, list[str]] = {}
    current = "header"
    for line in lines:
        if not line:
            continue
        clean = re.sub(r"[^a-zA-Z ]", "", line).strip().lower()
        matched = None
        if len(clean) <= 45 and clean in SECTION_HEADERS:
            matched = clean
        else:
            for section, headers in SECTION_HEADERS.items():
                if len(line) <= 60 and any(line.strip().lower().rstrip(":").endswith(h) or line.strip().lower().rstrip(":") == h for h in headers):
                    matched = section
                    break
        if matched:
            mapped = "summary" if matched == "summary" else matched
            current = mapped if mapped != "experience" else "experience"
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line)
    return sections


def _parse_education(lines: list[str]) -> list[Education]:
    results: list[Education] = []
    for line in lines:
        if _EDUCATION_LINE_RE.search(line):
            edu = Education(degree=line.strip())
            year = _YEAR_RE.search(line)
            if year:
                edu.year = year.group(0)
            cgpa = _CGPA_RE.search(line)
            if cgpa:
                edu.score = f"{cgpa.group(1)} {cgpa.group(2)}"
            results.append(edu)
    # Attach institution lines following a degree line.
    for i, edu in enumerate(results):
        pass
    return results


def _parse_experience(lines: list[str]) -> list[ExperienceItem]:
    items: list[ExperienceItem] = []
    for line in lines:
        if len(line) < 15:
            continue
        item = ExperienceItem(description=line.strip())
        items.append(item)
    return items[:12]


def _extract_title(line: str) -> str | None:
    """Extract a project title from 'Title - description' or 'Title: description'."""
    for sep in (":", " - ", " – ", " — ", "|"):
        if sep in line:
            head = line.split(sep, 1)[0].strip()
            if 3 <= len(head) <= 60 and not head.endswith(".") and head[0].isalnum():
                return head
    return None


def _is_project_title(line: str) -> bool:
    if len(line) > 160:
        return False
    title = _extract_title(line)
    return title is not None and len(line) - len(title) > 15


def _line_to_project(line: str) -> Project:
    project = Project()
    title = _extract_title(line)
    if title:
        project.name = title
        remainder = line[len(title):].lstrip(":-|–— ").strip()
        project.description = remainder or line
    else:
        project.description = line
    return project


def _parse_projects(lines: list[str]) -> list[Project]:
    """Group consecutive lines into projects; a new project starts when a
    title-like line appears ('Title - description' / 'Title: description')."""
    projects: list[Project] = []
    current: Project | None = None
    for line in lines:
        if not current:
            current = _line_to_project(line)
            projects.append(current)
            continue
        if _is_project_title(line):
            current = _line_to_project(line)
            projects.append(current)
        else:
            current.description = ((current.description or "") + " " + line).strip()
    for project in projects:
        techs = fuzzy_find_skill(project.description or "")
        project.technologies = techs[:12]
    return projects[:10]


def rule_based_resume_profile(text: str) -> ResumeProfile:
    """Extract a structured profile from raw resume text without AI."""
    sections = split_sections(text)
    profile = ResumeProfile(extraction_method="rule_based")

    # Email / phone
    email_match = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    if email_match:
        profile.email = email_match.group(0)
    phone_match = re.search(r"(?:\+?\d{1,3}[\s\-]?)?(?:\d[\s\-]?){9,12}\d", text)
    if phone_match:
        digits = re.sub(r"\D", "", phone_match.group(0))
        if 10 <= len(digits) <= 13:
            profile.phone = phone_match.group(0).strip()

    # Name: first plausible line of the header section
    for line in sections.get("header", []):
        clean = line.strip()
        if (
            2 <= len(clean) <= 48
            and re.search(r"[a-zA-Z]{2,}", clean)
            and "@" not in clean
            and not re.search(r"\d{4}", clean)
            and not re.search(r"(curriculum|vitae|resume)", clean, re.IGNORECASE)
            and sum(ch.isdigit() for ch in clean) <= 3
        ):
            profile.full_name = clean.title() if clean.isupper() else clean
            break

    # Summary
    summary_lines = sections.get("summary", [])
    if summary_lines:
        profile.professional_summary = " ".join(summary_lines)[:1200]

    # Skills
    skills_text = " ".join(sections.get("skills", []))
    if not skills_text:
        skills_text = text
    skills = fuzzy_find_skill(skills_text)
    profile.technical_skills = skills
    for skill in skills:
        if skill in ("Python", "Java", "JavaScript", "TypeScript", "C", "C++", "C#", "Go", "Rust", "PHP", "Kotlin", "Swift", "Ruby", "Dart", "SQL"):
            if skill not in profile.programming_languages:
                profile.programming_languages.append(skill)
        if skill in ("React", "Next.js", "Angular", "Vue.js", "Node.js", "Express", "NestJS", "Django", "Flask", "FastAPI", "Spring Boot", "Flutter", "Bootstrap", "Tailwind CSS"):
            if skill not in profile.frameworks:
                profile.frameworks.append(skill)
        if skill not in profile.tools_and_technologies and skill not in profile.frameworks and skill not in profile.programming_languages:
            profile.tools_and_technologies.append(skill)

    profile.education = _parse_education(sections.get("education", []))
    profile.projects = _parse_projects(sections.get("projects", []))
    profile.internships = _parse_experience(sections.get("internships", []))
    profile.work_experience = _parse_experience(sections.get("experience", []))
    profile.certifications = [c for c in sections.get("certifications", []) if 3 < len(c) < 200][:12]
    profile.achievements = [a for a in sections.get("achievements", []) if 3 < len(a) < 250][:12]
    return profile


# --------------------------------------------------------------------------
# Job description analysis (rule-based)
# --------------------------------------------------------------------------
def rule_based_job_info(text: str) -> JobDescriptionInfo:
    info = JobDescriptionInfo(extraction_method="rule_based")
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # Role: line containing typical job-title markers.
    title_markers = ("hiring", "looking for", "job title", "position", "role", "vacancy", "opening")
    for i, line in enumerate(lines[:15]):
        lower = line.lower()
        if any(m in lower for m in title_markers) and 8 < len(line) < 120:
            info.role = re.sub(r"^(we are|we're)\s*(hiring|looking for)[:\s]*", "", line, flags=re.IGNORECASE).strip(" :|-")
            break
    if not info.role and lines:
        for line in lines[:6]:
            if 8 < len(line) < 90 and not "@" in line and not line.lower().startswith(("http", "www")):
                info.role = line
                break

    # Company.
    company_match = re.search(r"(?:company|organisation|organization)\s*[:\-]\s*([A-Za-z0-9 .,&()\-]{2,60})", text, re.IGNORECASE)
    if company_match:
        info.company = company_match.group(1).strip()

    # Experience requirement.
    exp_match = re.search(r"(\d+\s*\+?\s*(?:to\s*\d+\s*\+?\s*)?(?:year|yr)s?(?:\s+of\s+experience)?|\d+\s*-\s*\d+\s*years?)", text, re.IGNORECASE)
    if exp_match:
        info.experience_requirements = exp_match.group(0).strip()

    # Education requirement.
    edu_line = next((l for l in lines if _EDUCATION_LINE_RE.search(l) and any(k in l.lower() for k in ("degree", "b.tech", "b.e", "mca", "bca", "bachelor", "master", "graduate", "qualification"))), None)
    if edu_line:
        info.education_requirements = edu_line[:200]

    # Skills - split into required/preferred by proximity to keywords.
    all_skills = fuzzy_find_skill(text)
    preferred_block = ""
    pref_match = re.search(r"(good to have|nice to have|preferred|plus points?|bonus)(.*?)(responsibilit|qualification|about us|$)", text, re.IGNORECASE | re.DOTALL)
    if pref_match:
        preferred_block = pref_match.group(2)
    preferred = set(fuzzy_find_skill(preferred_block)) if preferred_block else set()
    info.required_skills = [s for s in all_skills if s not in preferred]
    info.preferred_skills = [s for s in all_skills if s in preferred]

    # Responsibilities / qualifications bullets.
    bullets = [l.lstrip("•-–* ").strip() for l in lines]
    resp_block = re.search(r"(responsibilit(?:y|ies)|what you.?ll do|key duties)(.*?)(requirement|qualification|skill|about|benefit|$)", text, re.IGNORECASE | re.DOTALL)
    if resp_block:
        info.responsibilities = [
            l.lstrip("•-–* ").strip()
            for l in resp_block.group(2).splitlines()
            if 25 < len(l.strip()) < 300
        ][:12]
    qual_block = re.search(r"(requirement|qualification|what we.?re looking for|who you are)(.*?)(benefit|about us|why join|responsibilit|$)", text, re.IGNORECASE | re.DOTALL)
    if qual_block:
        info.qualifications = [
            l.lstrip("•-–* ").strip()
            for l in qual_block.group(2).splitlines()
            if 25 < len(l.strip()) < 300
        ][:12]
    return info


# --------------------------------------------------------------------------
# Matching (rule-based)
# --------------------------------------------------------------------------
def _skill_evidence_text(profile: ResumeProfile) -> str:
    """Text of the resume parts that DEMONSTRATE skills (projects, experience)."""
    parts: list[str] = []
    for project in profile.projects:
        parts.append(f"{project.name or ''} {project.description or ''}")
    for item in [*profile.internships, *profile.work_experience]:
        parts.append(f"{item.role or ''} {item.organization or ''} {item.description or ''}")
    return " ".join(parts)


def rule_based_match(profile: ResumeProfile, job_info: JobDescriptionInfo, resume_text: str) -> MatchResult:
    evidence_text = _skill_evidence_text(profile)
    skills_section_text = " ".join(profile.technical_skills + profile.frameworks + profile.tools_and_technologies)

    required = job_info.required_skills or []
    preferred = job_info.preferred_skills or []
    pool = [s for s in dict.fromkeys(required + preferred)]

    matched: list = []
    partial: list = []
    missing: list = []
    demonstrated_in_project = 0

    for skill in pool:
        importance = "high" if skill in required[: max(6, len(required) // 2)] else ("high" if skill in required else "medium")
        canon = normalize_skill(skill) or skill
        in_skills_list = canon.lower() in skills_section_text.lower()
        in_evidence = canon.lower() in evidence_text.lower()

        if in_evidence:
            snippet = _find_evidence_snippet(evidence_text, canon)
            matched.append({"skill": canon, "evidence": snippet, "match_type": "demonstrated"})
            if skill in required:
                demonstrated_in_project += 1
        elif in_skills_list:
            partial.append(
                {
                    "skill": canon,
                    "evidence": "Listed in the skills section only",
                    "match_type": "partial",
                    "reason_partial": "Mentioned in the skills list but not demonstrated through projects or experience",
                }
            )
        else:
            reason = f"Required by the job description" if skill in required else "Preferred by the job description"
            missing.append({"skill": canon, "importance": importance, "reason": reason})

    # ---- deterministic sub-scores
    if pool:
        required_weight = {s: 1.0 for s in required}
        preferred_weight = {s: 0.5 for s in preferred if s not in required}
        total_weight = sum(required_weight.get(s, 0.0) + preferred_weight.get(s, 0.0) for s in pool)
        gained = 0.0
        for entry in matched:
            s = entry["skill"]
            gained += required_weight.get(s, 0.0) + preferred_weight.get(s, 0.0)
        for entry in partial:
            s = entry["skill"]
            gained += 0.5 * (required_weight.get(s, 0.0) + preferred_weight.get(s, 0.0))
        technical = round(100 * gained / total_weight) if total_weight else 50
    else:
        technical = 50

    # Education
    education_score = 50
    if job_info.education_requirements:
        job_edu = job_info.education_requirements.lower()
        resume_edu = " ".join(f"{e.degree or ''} {e.institution or ''}" for e in profile.education).lower()
        if resume_edu:
            if any(k in resume_edu for k in ("m.tech", "mca", "master", "m.sc", "mba")):
                education_score = 90 if any(k in job_edu for k in ("bachelor", "b.tech", "b.e", "b.sc", "bca", "graduate")) else 80
            elif any(k in resume_edu for k in ("b.tech", "b.e", "b.sc", "bca", "bachelor")):
                education_score = 90 if any(k in job_edu for k in ("b.tech", "b.e", "b.sc", "bca", "bachelor", "graduate")) else 70
            else:
                education_score = 55
        else:
            education_score = 40

    # Experience (crude: count experience items & internships)
    exp_items = len(profile.internships) + len(profile.work_experience)
    if job_info.experience_requirements and "0" in job_info.experience_requirements[:2]:
        experience_score = min(100, 70 + exp_items * 15)
    elif exp_items >= 2:
        experience_score = 85
    elif exp_items == 1:
        experience_score = 65
    elif profile.projects:
        experience_score = 45
    else:
        experience_score = 25

    # Project relevance
    if required:
        project_relevance = round(100 * demonstrated_in_project / max(1, len(required)))
        project_relevance = max(project_relevance, 15 if profile.projects else 0)
    else:
        project_relevance = 60 if profile.projects else 30

    overall = round(
        settings.weight_technical_skills * technical
        + settings.weight_education * education_score
        + settings.weight_experience * experience_score
        + settings.weight_project_relevance * project_relevance
    )
    overall = max(0, min(100, overall))

    breakdown = [
        ScoreDimension(name="Technical skills", score=technical, weight=settings.weight_technical_skills,
                       explanation=f"{len(matched)} matched, {len(partial)} partial, {len(missing)} missing of {len(pool)} job skills"),
        ScoreDimension(name="Education", score=education_score, weight=settings.weight_education,
                       explanation=f"Resume education vs requirement: {job_info.education_requirements or 'not specified'}"),
        ScoreDimension(name="Experience", score=experience_score, weight=settings.weight_experience,
                       explanation=f"{exp_items} internship/experience entr{'y' if exp_items == 1 else 'ies'} found in resume"),
        ScoreDimension(name="Project relevance", score=project_relevance, weight=settings.weight_project_relevance,
                       explanation=f"{demonstrated_in_project} of {len(required)} required skills demonstrated in projects"),
    ]

    recommendations: list[str] = []
    for entry in missing[:4]:
        recommendations.append(f"Build a practical project using {entry['skill']} and add it to your resume.")
    for entry in partial[:3]:
        recommendations.append(f"Strengthen evidence for {entry['skill']} by describing how you used it in a project or internship.")
    if not recommendations:
        recommendations.append("Your profile aligns well with this role - focus on interview preparation and communicating your projects clearly.")

    unmet = [f"{e['skill']} - {e['reason']}" for e in missing if e["importance"] == "high"]

    explanation = (
        f"Weighted score = {int(settings.weight_technical_skills * 100)}% technical ({technical}) + "
        f"{int(settings.weight_education * 100)}% education ({education_score}) + "
        f"{int(settings.weight_experience * 100)}% experience ({experience_score}) + "
        f"{int(settings.weight_project_relevance * 100)}% project relevance ({project_relevance}). "
        f"Computed with deterministic keyword matching (rule-based mode)."
    )

    return MatchResult(
        overall_match_score=overall,
        technical_skill_score=max(0, min(100, technical)),
        education_score=max(0, min(100, education_score)),
        experience_score=max(0, min(100, experience_score)),
        project_relevance_score=max(0, min(100, project_relevance)),
        matched_skills=[m for m in matched],
        partially_matched_skills=[p for p in partial],
        missing_skills=[m for m in missing],
        resume_evidence=[f"Matched {e['skill']}: {e['evidence']}" for e in matched[:6]],
        unmet_requirements=unmet[:8],
        recommendations=recommendations[:6],
        score_breakdown=breakdown,
        score_explanation=explanation,
        analysis_method="rule_based",
    )


def _find_evidence_snippet(evidence_text: str, skill: str) -> str:
    """Return the sentence where the skill is demonstrated."""
    for sentence in re.split(r"(?<=[.!?])\s+", evidence_text):
        if skill.lower() in sentence.lower():
            return sentence.strip()[:220]
    return "Found in project/experience content"


# --------------------------------------------------------------------------
# Skill gaps (rule-based)
# --------------------------------------------------------------------------
LEARNING_GUIDE: dict[str, tuple[str, str, str]] = {
    "Docker": ("Learn images, containers, volumes and Dockerfiles; then containerise one of your existing projects.", "Containerise your resume project with a Dockerfile and publish the image to Docker Hub.", "2-3 weeks"),
    "Kubernetes": ("Understand pods, deployments, services and ingress; use a local cluster (minikube/kind).", "Deploy your containerised app to a local Kubernetes cluster with a deployment + service YAML.", "3-4 weeks"),
    "AWS": ("Start with EC2, S3, IAM and RDS via the free tier; follow the 'Cloud Practitioner' learning path.", "Host your project API on an EC2 instance with S3 for static assets.", "3-4 weeks"),
    "React": ("Learn components, hooks, state and routing; rebuild a small UI you already know.", "Build a dashboard that consumes your own REST API.", "3-4 weeks"),
    "Node.js": ("Learn the event loop, Express routing, middleware and REST conventions.", "Create a REST API with auth (JWT) for one of your projects.", "2-3 weeks"),
    "TypeScript": ("Learn types, interfaces, generics and tsconfig basics; convert a small JS project.", "Convert an existing JavaScript project to TypeScript with strict mode.", "2 weeks"),
    "SQL": ("Practise SELECT/JOIN/GROUP BY and indexing basics on a sample database.", "Design and query a normalised schema for a mini e-commerce or library app.", "2-3 weeks"),
    "MongoDB": ("Learn documents, collections, CRUD and aggregation pipelines.", "Add a MongoDB-backed data layer to one of your projects.", "2 weeks"),
    "Python": ("Core syntax, data structures, OOP and a web framework (Flask/FastAPI).", "Build a small REST API with FastAPI and SQLite.", "3-4 weeks"),
    "Java": ("Learn core Java, OOP, collections, then Spring Boot basics.", "Build a REST service with Spring Boot and an in-memory DB.", "4-6 weeks"),
    "Machine Learning": ("Learn regression, classification, evaluation metrics with scikit-learn.", "Train and compare models on a Kaggle dataset and document results.", "4-6 weeks"),
    "Deep Learning": ("Neural network basics, backprop, then CNNs with PyTorch or TensorFlow.", "Build an image classifier and deploy it behind a simple API.", "6-8 weeks"),
    "NLP": ("Text preprocessing, embeddings, transformers basics.", "Build a resume-vs-job-description similarity tool.", "4-6 weeks"),
    "System Design": ("Study caching, load balancing, DB indexing and scaling patterns.", "Write a design document for scaling one of your projects to 1M users.", "3-4 weeks"),
    "Git": ("Learn branching, merging, pull requests and conflict resolution.", "Contribute a real PR to an open-source repository or maintain your project with a proper branching flow.", "1 week"),
    "REST API": ("HTTP verbs, status codes, pagination, and API design best practices.", "Design and document a public API for one of your projects.", "1-2 weeks"),
    "CI/CD": ("Learn GitHub Actions workflows: build, test, deploy.", "Add automated tests + a deploy workflow to one of your GitHub projects.", "2 weeks"),
    "Data Structures": ("Arrays, linked lists, trees, graphs, hashing; practise on LeetCode easy/medium.", "Solve 50 curated problems and write short notes on patterns.", "4-6 weeks"),
}


def rule_based_skill_gaps(match_result: MatchResult, job_info: JobDescriptionInfo) -> list[SkillGapItem]:
    gaps: list[SkillGapItem] = []
    for entry in match_result.missing_skills:
        skill = entry.skill
        approach, project, duration = LEARNING_GUIDE.get(
            skill,
            (
                f"Take a structured course or official documentation path for {skill}, then practise deliberately.",
                f"Add {skill} to one of your existing projects or start a small dedicated project that uses it.",
                "2-4 weeks",
            ),
        )
        gaps.append(
            SkillGapItem(
                skill=skill,
                importance=entry.importance,
                job_requirement_reason=entry.reason,
                current_resume_evidence=None,
                learning_approach=approach,
                suggested_project=project,
                estimated_learning_duration=duration,
            )
        )
    for entry in match_result.partially_matched_skills:
        skill = entry.skill
        gaps.append(
            SkillGapItem(
                skill=skill,
                importance="medium",
                job_requirement_reason="Job requires this skill and it is only listed, not demonstrated",
                current_resume_evidence=entry.evidence,
                learning_approach=f"Strengthen {skill} by using it in a real project and describing your specific contribution.",
                suggested_project=f"Extend an existing project with {skill} and quantify what you built with it.",
                estimated_learning_duration="1-3 weeks",
            )
        )
    return gaps[:12]


# --------------------------------------------------------------------------
# Bullet optimization (rule-based)
# --------------------------------------------------------------------------
WEAK_STRONG_VERBS: list[tuple[str, str]] = [
    (r"\bworked on\b", "Developed"),
    (r"\bworked with\b", "Utilised"),
    (r"\bmade\b", "Built"),
    (r"\bhelped\b", "Supported"),
    (r"\bdid\b", "Executed"),
    (r"\bused\b", "Applied"),
    (r"\bcreated\b", "Developed"),
    (r"\bwas part of\b", "Contributed to"),
    (r"\bresponsible for\b", "Owned"),
    (r"\bhandled\b", "Managed"),
    (r"\bparticipated in\b", "Contributed to"),
    (r"\binvolved in\b", "Contributed to"),
]

ACTION_STARTERS = ["Developed", "Built", "Implemented", "Designed", "Engineered", "Delivered"]


def rule_based_optimize_bullets(bullets: list[tuple[str, str]], job_keywords: list[str]) -> list[BulletOptimization]:
    """`bullets` is a list of (section, text). Rule-based rewrite: strong
    action verbs, capitalisation, keyword surfacing. No invented content."""
    results: list[BulletOptimization] = []
    job_keywords_lower = [k.lower() for k in job_keywords]
    for section, original in bullets:
        text = original.strip()
        if len(text) < 12:
            continue
        optimized = text
        changes: list[str] = []
        for pattern, strong in WEAK_STRONG_VERBS:
            new = re.sub(pattern, strong, optimized, count=1, flags=re.IGNORECASE)
            if new != optimized:
                changes.append(f'replaced a weak verb with "{strong}"')
                optimized = new
        # Capitalise first letter.
        if optimized and optimized[0].islower():
            optimized = optimized[0].upper() + optimized[1:]
        # Ensure it starts with an action verb.
        first_word = optimized.split(" ", 1)[0].lower().strip(":.,")
        if first_word in ("i", "the", "a", "an", "my", "this", "it", "and", "also") and ACTION_STARTERS:
            optimized = f"{ACTION_STARTERS[len(results) % len(ACTION_STARTERS)]} {optimized[0].lower() + optimized[1:] if optimized else ''}"
            changes.append("starts with a strong action verb")
        if optimized == original.strip() and not changes:
            # Fall back to a light cleanup suggestion.
            optimized = original.strip().rstrip(".") + "."
            if optimized == original.strip():
                continue
            changes.append("consistent punctuation")
        highlighted = [k for k in job_keywords if k.lower() in optimized.lower()][:6]
        results.append(
            BulletOptimization(
                section=section,
                original_bullet=original.strip(),
                optimized_bullet=optimized,
                improvement_rationale=("Rule-based polish: " + "; ".join(changes)) if changes else "Rule-based polish",
                keywords_highlighted=highlighted,
                method="rule_based",
            )
        )
    return results[:14]


# --------------------------------------------------------------------------
# Interview questions (rule-based)
# --------------------------------------------------------------------------
def rule_based_interview_questions(
    profile: ResumeProfile,
    job_info: JobDescriptionInfo,
    categories: list[str],
    per_category: int,
) -> list[InterviewQuestion]:
    questions: list[InterviewQuestion] = []
    top_skills = list(dict.fromkeys(job_info.required_skills))[:5] or profile.technical_skills[:5]
    projects = [p for p in profile.projects if (p.name or p.description)][:3]

    def add(question: str, category: str, difficulty: str, why: str, concepts: list[str], structure: str) -> None:
        questions.append(
            InterviewQuestion(
                question=question,
                category=category,  # type: ignore[arg-type]
                difficulty=difficulty,  # type: ignore[arg-type]
                why_asked=why,
                key_concepts=concepts,
                answer_structure=structure,
                method="rule_based",
            )
        )

    for skill in top_skills:
        if len([q for q in questions if q.category == "technical"]) >= per_category and "technical" in categories:
            break
        if "technical" in categories:
            add(
                f"Explain {skill} and how you have used it. What are its core concepts and common pitfalls?",
                "technical",
                "medium",
                f"The job description lists {skill} as a required skill, so expect fundamentals questions.",
                [skill],
                "1) Define it in one sentence 2) Give a concrete example from your work 3) Mention one pitfall or best practice.",
            )
        if "programming" in categories:
            add(
                f"Write a short program or algorithm of your choice that demonstrates your understanding of {skill} or of a data structure you used with it.",
                "programming",
                "medium",
                "Employers verify hands-on coding ability for listed skills.",
                [skill, "Data Structures"],
                "1) Clarify the problem 2) Outline your approach 3) Write clean code 4) Discuss complexity.",
            )

    for project in projects:
        if "project" in categories:
            add(
                f"Walk me through your project '{project.name or 'your project'}'. What was your role, what technologies did you use and what did you learn?",
                "project",
                "easy",
                "Interviewers probe resume projects to verify depth and genuine contribution.",
                project.technologies[:5] or ["Project structure", "Problem solving"],
                "1) Problem & goal 2) Your specific role 3) Tech choices and why 4) Challenges & fixes 5) Outcome and learnings.",
            )
            add(
                f"What was the hardest technical challenge in '{project.name or 'your project'}' and how did you solve it?",
                "project",
                "hard",
                "Tests problem-solving depth beyond the happy path.",
                ["Debugging", "Design decisions"],
                "1) Describe the challenge concretely 2) Options you considered 3) The fix 4) What you would do differently.",
            )

    if "hr" in categories:
        add(
            "Tell me about yourself and why you want to work with us in this role.",
            "hr",
            "easy",
            "Standard opener that tests preparation and communication.",
            ["Self-introduction", "Motivation"],
            "1) Present: studies/focus 2) Past: key projects/internships 3) Future: why this role/company.",
        )
        add(
            "What are your strengths and weaknesses as a fresher joining this organisation?",
            "hr",
            "easy",
            "Assesses self-awareness and honesty.",
            ["Self-awareness", "Growth mindset"],
            "1) 1-2 strengths with proof 2) One real weakness 3) Concrete steps you are taking to improve it.",
        )
        add(
            "Where do you see yourself in three years, and how does this role fit that plan?",
            "hr",
            "easy",
            "Checks goal alignment and seriousness about the role.",
            ["Career planning"],
            "1) Skills you want to build 2) Responsibility you want to grow into 3) Tie back to this role.",
        )

    if "behavioral" in categories:
        add(
            "Describe a situation where you had to work under a tight deadline. What did you do?",
            "behavioral",
            "medium",
            "Behavioural questions test the STAR structure and time management.",
            ["STAR method", "Prioritisation"],
            "Situation -> Task -> Action -> Result; keep it under 2 minutes and end with the measurable outcome.",
        )
        add(
            "Tell me about a time you disagreed with a teammate. How was it resolved?",
            "behavioral",
            "medium",
            "Tests collaboration and conflict resolution.",
            ["Communication", "Empathy"],
            "Situation -> your action -> compromise reached -> what you learned about teamwork.",
        )

    if "scenario" in categories:
        add(
            "You join a team whose codebase has no documentation and an urgent bug arrives. How do you proceed?",
            "scenario",
            "hard",
            "Tests practical judgement, debugging methodology and communication.",
            ["Debugging", "Prioritisation", "Stakeholder communication"],
            "1) Reproduce & scope the bug 2) Communicate impact 3) Investigate minimally 4) Fix, test, document.",
        )
        if top_skills:
            add(
                f"Your team must choose a technology for a new service and you know {top_skills[0]}. How do you evaluate and recommend?",
                "scenario",
                "hard",
                "Tests architecture thinking beyond personal preference.",
                ["Trade-off analysis", "Scalability"],
                "1) Requirements 2) Options with trade-offs 3) Recommendation with reasoning 4) Risks & mitigation.",
            )

    return questions[: per_category * max(1, len(categories))]
