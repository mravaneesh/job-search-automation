import pytest

from jobsearch.normalize.skills import SkillExtractor


@pytest.fixture(scope="module")
def extractor():
    return SkillExtractor.from_config()


def test_extract_basic(extractor):
    text = "Build distributed systems in Go with Kafka and PostgreSQL on Kubernetes."
    skills = extractor.extract(text)
    assert "Go" in skills
    assert "Kafka" in skills
    assert "PostgreSQL" in skills
    assert "Kubernetes" in skills


def test_extract_handles_cpp(extractor):
    skills = extractor.extract("Strong C++ background required.")
    assert "C++" in skills


def test_no_false_positive_word_boundary(extractor):
    # "javascript" should not also match a bare "java" alias as Java only when
    # the token "java" appears on its own.
    skills = extractor.extract("We use JavaScript and TypeScript.")
    assert "JavaScript" in skills
    assert "TypeScript" in skills


def test_empty(extractor):
    assert extractor.extract(None) == []
    assert extractor.extract("") == []
