import pytest

from jobsearch.normalize.roles import RoleClassifier


@pytest.fixture(scope="module")
def classifier():
    return RoleClassifier.from_config()


@pytest.mark.parametrize(
    "title,expected",
    [
        ("Android Engineer", "android"),
        ("Senior Android Developer", "android"),
        ("Machine Learning Engineer", "ai_ml"),
        ("Applied Scientist, NLP", "ai_ml"),
        ("Backend Engineer", "backend"),
        ("Distributed Systems Engineer", "backend"),
        ("Office Manager", None),
        ("Technical Recruiter", None),
    ],
)
def test_classify_by_title(classifier, title, expected):
    assert classifier.classify(title) == expected


def test_description_fallback(classifier):
    # Neutral title, but description carries a backend signal -> backend wins
    # (backend outranks the generic "software" catch-all in priority).
    desc = "You will build microservices architecture"
    assert classifier.classify("Engineer II", desc) == "backend"


def test_generic_software_title_collected(classifier):
    # Generic SWE titles are now collected under the catch-all "software" role.
    assert classifier.classify("Software Engineer", "Join our team") == "software"
    assert classifier.classify("Member of Technical Staff", "build things") == "software"


def test_non_software_title_dropped(classifier):
    # Truly non-engineering titles are still dropped.
    assert classifier.classify("Office Manager", "Join our team") is None
