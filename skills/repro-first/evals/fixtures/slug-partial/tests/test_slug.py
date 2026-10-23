from slugger import slugify


def test_basic():
    assert slugify("Hello World") == "hello-world"


def test_accents():
    assert slugify("Crème Brûlée") == "creme-brulee"


def test_multiple_spaces():
    assert slugify("a   b") == "a-b"


def test_custom_sep():
    assert slugify("a b", sep="_") == "a_b"
