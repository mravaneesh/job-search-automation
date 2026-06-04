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
    # Generic title, but description carries a backend signal.
    desc = "You will build microservices architecture"
    assert classifier.classify("Software Engineer", desc) == "backend"


def test_generic_title_no_signal_dropped(classifier):
    assert classifier.classify("Software Engineer", "Join our team") is None
