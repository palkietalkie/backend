"""Lock the daily-content topics catalog so a careless rename doesn't break the iOS xcstrings entries or the daily scheduler."""

from app.pipelines.daily_content.constants import POOL_SAMPLE_SIZE, POOL_TOPICS, TOPICS


def test_topics_contains_quizzes() -> None:
    assert "quizzes" in TOPICS


def test_pool_topics_is_subset_of_topics() -> None:
    assert POOL_TOPICS.issubset(set(TOPICS))


def test_pool_topics_currently_only_quizzes() -> None:
    # Quizzes are time-insensitive; news topics rotate daily. If a new pool-topic is added, update this test AND the daily scheduler that decides which fetcher to call.
    assert frozenset({"quizzes"}) == POOL_TOPICS


def test_pool_sample_size_is_positive() -> None:
    assert POOL_SAMPLE_SIZE > 0


def test_topics_is_immutable_tuple() -> None:
    assert isinstance(TOPICS, tuple)
