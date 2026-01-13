import enum
import typing

import pytest

from entities import Entity, Field


class SimpleTestEntity(Entity):
    a: int
    b: str
    c: float


class ComplexTestEntity(Entity):
    simple: SimpleTestEntity
    a: int


@pytest.mark.unit
def test_simple_entity():
    ent = SimpleTestEntity(a=1, b="asdf", c=1.4)
    assert ent.a == 1
    assert ent.b == "asdf"
    assert ent.c == 1.4

    with pytest.raises(TypeError):
        SimpleTestEntity(a=1, b=2, c=1.4)

    with pytest.raises(TypeError):
        SimpleTestEntity(a="asdf", b=2, c=1.4)


@pytest.mark.unit
def test_complex_entity():
    ent = ComplexTestEntity(simple=SimpleTestEntity(a=1, b="asdf", c=1.4), a=1)

    assert ent.simple.a == 1
    assert ent.simple.b == "asdf"
    assert ent.simple.c == 1.4
    assert ent.a == 1

    ent = ComplexTestEntity(simple={"a": 1, "b": "asdf", "c": 1.4}, a=1)

    assert ent.simple.a == 1
    assert ent.simple.b == "asdf"
    assert ent.simple.c == 1.4
    assert ent.a == 1

    with pytest.raises(TypeError):
        ComplexTestEntity(simple={"a": 1, "c": 1.4}, a=1)


class ListTestEntity(Entity):
    shallow: list[int]
    deep: list[list[int]]


@pytest.mark.unit
def test_list_entity():
    ent = ListTestEntity(shallow=[1, 2, 3], deep=[[1, 2], [2, 3], [3, 4]])
    assert ent.shallow == [1, 2, 3]
    assert ent.deep == [[1, 2], [2, 3], [3, 4]]

    with pytest.raises(TypeError):
        ListTestEntity(shallow=["asdf", 2, 3], deep=[[1, 2]])

    with pytest.raises(TypeError):
        ListTestEntity(shallow=[1, 2, 3], deep=[[1, "asdf"]])


class MappingTestEntity(Entity):
    shallow: dict[str, str]
    deep: dict[str, dict[str, str]]

@pytest.mark.unit
def test_mapping_entity():
    ent = MappingTestEntity(shallow={"a": "b"}, deep={"a": {"b": "c"}})
    assert ent.shallow == {"a": "b"}
    assert ent.deep == {"a": {"b": "c"}}

    with pytest.raises(TypeError):
        MappingTestEntity(shallow={"a": 1}, deep={"a": {"b": "c"}})

    with pytest.raises(TypeError):
        MappingTestEntity(shallow={"a": "b"}, deep={"a": {"b": 1}})

    with pytest.raises(TypeError):
        MappingTestEntity(shallow={"a": "b"}, deep={"a": 1})


class MappingListTestEntity(Entity):
    sequence: dict[str, list[int]]


@pytest.mark.unit
def test_mapping_list_entity():
    ent = MappingListTestEntity(sequence={"a": [1, 2, 3]})
    assert ent.sequence == {"a": [1, 2, 3]}

    with pytest.raises(TypeError):
        MappingListTestEntity(sequence={"asdf": 1})


class OptionalTestEntity(Entity):
    optional_int: int | None
    optional_list: list[int] | None

    alt_optional_int: typing.Optional[int]


@pytest.mark.unit
def test_optional_entity():
    ent = OptionalTestEntity(optional_int=None, optional_list=None, alt_optional_int=None)
    assert ent.optional_int is None
    assert ent.optional_list is None

    ent = OptionalTestEntity(optional_int=1, optional_list=[2, 3, 4], alt_optional_int=5)
    assert ent.optional_int == 1
    assert ent.optional_list == [2, 3, 4]
    assert ent.alt_optional_int == 5
    
    with pytest.raises(TypeError):
        OptionalTestEntity(optional_int="asdf", optional_list=None, alt_optional_int=None)


class TestIntEnum(enum.IntEnum):
    one = 1
    two = 2
    three = 3


class TestStrEnum(enum.StrEnum):
    asdf = "asdf"
    qwerty = "qwerty"


class EnumEntity(Entity):
    int_enum: TestIntEnum
    str_enum: TestStrEnum


@pytest.mark.unit
def test_enum_entity():
    ent = EnumEntity(int_enum=TestIntEnum.one, str_enum=TestStrEnum.asdf)
    assert ent.int_enum == TestIntEnum.one
    assert ent.str_enum == TestStrEnum.asdf

    ent = EnumEntity(int_enum=2, str_enum="qwerty")
    assert ent.int_enum == TestIntEnum.two
    assert ent.str_enum == TestStrEnum.qwerty

    with pytest.raises(ValueError):
        EnumEntity(int_enum=5, str_enum=TestStrEnum.asdf)

    with pytest.raises(ValueError):
        EnumEntity(int_enum=TestIntEnum.three, str_enum="blah")

