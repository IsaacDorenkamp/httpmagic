from __future__ import annotations
import collections.abc
import copy
import enum
import json
import types
import typing


T = typing.TypeVar("T")


NONE_TYPE = type(None)
NULL = object()


class FieldInfo:
    name: str
    types: tuple[type, ...]
    optional: bool
    default: tuple[bool, typing.Any]

    def __init__(self, name: str, optional: bool = False, default: typing.Any = NULL):
        self.name = name
        self.optional = optional

        if default is not NULL:
            self.default = True, default
        else:
            self.default = False, None

    def validate(self, value: typing.Any):
        exact_type = type(value)
        if exact_type in self.types:
            return value

        for valid_type in self.types:
            validated = self.validate_single(valid_type, value)
            if validated is not NULL:
                return validated

        raise TypeError("value '%s' does not match field type %s" % (str(value), str(self)))

    def __str__(self) -> str:
        result = " | ".join(tp.__name__ for tp in self.types)
        if self.optional:
            result = f"Optional[{result}]"
        return result

    def validate_single(self, single_type: type, value: typing.Any):
        origin_type = getattr(single_type, "__origin__", single_type)
        if self.optional and value is None:
            return None

        if issubclass(origin_type, Entity) and isinstance(value, dict):
            try:
                return single_type(**value)
            except (TypeError, ValueError):
                return NULL
        elif issubclass(origin_type, enum.Enum):
            return origin_type(value)
        elif issubclass(origin_type, collections.abc.Sequence):
            if isinstance(value, collections.abc.Iterable):
                return self.validate_sequence(single_type, value)
            else:
                raise TypeError("A Sequence type requires an Iterable value!")
        elif issubclass(origin_type, collections.abc.Mapping):
            if isinstance(value, collections.abc.Mapping):
                return self.validate_mapping(single_type, value)
            else:
                raise TypeError("A Mapping type requires a Mapping value!")
        else:
            if isinstance(value, origin_type):
                return value
            else:
                raise TypeError("'%s' does not validly belong to type %s" % (value, single_type))

    def validate_sequence(self, seq_type: type, value: typing.Iterable):
        if hasattr(seq_type, "__args__"):
            # validate element types
            element_type = seq_type.__args__[0]
            return seq_type(self.validate_single(element_type, element) for element in value)
        else:
            return seq_type(value)

    def validate_mapping(self, mapping_type: type, value: typing.Mapping):
        if hasattr(mapping_type, "__args__"):
            # validate keys and values
            key_type, value_type = mapping_type.__args__
            return mapping_type({ self.validate_single(key_type, key): self.validate_single(value_type, value) for key, value in value.items() })
        else:
            return mapping_type(value)


class EntityMeta(type):
    def __new__(cls, *args):
        new_type = super().__new__(cls, *args)
        new_type.__fields__ = {}

        hints = typing.get_type_hints(new_type)
        for name, field_type in hints.items():
            if (name.startswith("__") and name.endswith("__")):
                continue

            # check if user has manually defined this
            if hasattr(new_type, name):
                field = getattr(new_type, name)
                if not isinstance(field, FieldInfo):
                    raise TypeError("Expected a Field instance, got %s" % field)
                new_type.__fields__[name] = getattr(new_type, name)
            else:
                new_type.__fields__[name] = FieldInfo(name)

            if not new_type.__fields__[name].name:
                new_type.__fields__[name].name = name

            origin_field_type = getattr(field_type, "__origin__", field_type)
            if isinstance(origin_field_type, types.UnionType) or origin_field_type is typing.Union:
                field_types = field_type.__args__
                if NONE_TYPE in field_types:
                    field_types = tuple(tp for tp in field_types if tp is not NONE_TYPE)
                    new_type.__fields__[name].optional = True
                new_type.__fields__[name].types = field_types
            else:
                new_type.__fields__[name].types = (field_type,)

        for name, value in args[2].items():
            if name.startswith("__") and name.endswith("__"):
                continue

            if callable(value):
                continue

            if not isinstance(value, FieldInfo):
                raise TypeError("Expected a Field instance, got %s (%s)" % (value, name))

            if name not in new_type.__fields__:
                new_type.__fields__[name] = value

        return new_type


class Entity(metaclass=EntityMeta):
    __fields__: typing.ClassVar[dict[str, FieldInfo]]

    def __init__(self, **kwargs):
        for key, field in self.__fields__.items():
            if key not in kwargs:
                if field.default[0]:
                    setattr(self, key, field.default[1])
                    continue
                raise ValueError(f"missing value for field '{key}'")

            setattr(self, key, field.validate(kwargs[key]))
            kwargs.pop(key)
            
        if kwargs:
            keys = list(kwargs.keys())
            raise ValueError(f"entity {self.__name__} has no field {keys[0]}")

    def copy(self):
        return copy.deepcopy(self)


class EntityEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Entity):
            return {
                field.name: getattr(o, key)
                for key, field in o.__fields__.items()
            }

        return super().default(o)


EntityType = typing.TypeVar("EntityType", bound=Entity)


class EntityDecoder(json.JSONDecoder, typing.Generic[EntityType]):
    __args__: typing.ClassVar[tuple[type]]

    def __init__(self, *args, **kwargs):
        kwargs["object_pairs_hook"] = self.__object_pairs_hook
        super().__init__(*args, **kwargs)

    def __object_pairs_hook(self, pairs: list[tuple[str, EntityType]]):
        entity_type = self.__args__[0]
        values = dict(pairs)
        for key, field in entity_type.items():
            values[key] = field.validate(values[key])
        return values


def Field(
    name: str | None = None,
    optional: bool = False,
    default: typing.Any = NULL,
) -> typing.Any:
    return FieldInfo(name or "", optional, default)

