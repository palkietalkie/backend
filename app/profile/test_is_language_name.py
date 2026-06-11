from app.profile.is_language_name import is_language_name


def test_is_language_name_true_for_known() -> None:
    assert is_language_name("English")


def test_is_language_name_false_for_unknown() -> None:
    assert not is_language_name("Not A Real Language Name")
