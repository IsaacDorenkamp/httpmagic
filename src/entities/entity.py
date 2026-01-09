from __future__ import annotations
import collections.abc
import json
import typing

import logging


T = typing.TypeVar("T")


class Field(typing.Generic[T]):
    name: str
    tp: type

    def __init__(self, name: str):
        self.name = name
        self.tp = type(None)

    @property
    def is_entity(self):
        proper_type = getattr(self.tp, "__origin__", self.tp)
        logging.debug("PROPER TYPE:", proper_type)
        # TODO: figure out
        return issubclass(proper_type, Entity)

    def convert(self, value: typing.Any):
        if self.is_entity:
            if type(value) == self.tp:
                return value
            elif isinstance(value, dict):
                return self.tp(**value)
            else:
                raise TypeError("Cannot convert type '%s' to entity type '%s'" % (type(value), self.tp))
        else:
            if self.tp in (int, float):
                if type(value) in (int, float):
                    return self.tp(value)
                else:
                    raise TypeError("value must be numerical")
            elif self.tp == str:
                if type(value) != str:
                    raise TypeError("value is not a str")
                return value
            elif hasattr(self.tp, "__origin__") and issubclass(self.tp.__origin__, collections.abc.Sequence):
                return Field.convert_sequence(self.tp, value)
            elif hasattr(self.tp, "__origin__") and issubclass(self.tp.__origin__, collections.abc.Mapping):
                return Field.convert_mapping(self.tp, value)
            else:
                return self.tp(value)

    @staticmethod
    def convert_sequence(tp, value):
        if hasattr(tp, "__origin__"):
            element_type = tp.__args__[0]
            raw_type = getattr(element_type, "__origin__", element_type)
            if issubclass(raw_type, collections.abc.Sequence):
                return tp(Field.convert_sequence(element_type, element) for element in value)
            elif issubclass(raw_type, collections.abc.Mapping):
                return tp(Field.convert_mapping(element_type, element) for element in value)
            else:
                if any(not isinstance(element, raw_type) for element in value):
                    raise TypeError("all elements must match type %s" % tp)
                return tp(value)
        else:
            if not isinstance(value, tp):
                raise TypeError("value does not match type %s" % tp)
            return tp(value) 

    @staticmethod
    def convert_mapping(tp, value):
        if hasattr(tp, "__origin__"):
            if not isinstance(value, tp.__origin__):
                raise TypeError("value does not match type %s" % tp)
            key_type = tp.__args__[0]
            value_type = tp.__args__[1]

            raw_key_type = getattr(key_type, "__origin__", key_type)
            raw_value_type = getattr(value_type, "__origin__", value_type)
            if issubclass(raw_key_type, collections.abc.Sequence):
                keys = [Field.convert_sequence(key_type, element) for element in value.keys()]
            elif issubclass(raw_key_type, collections.abc.Mapping):
                keys = [Field.convert_mapping(key_type, element) for element in value.keys()]
            else:
                if any(not isinstance(element, raw_key_type) for element in value.keys()):
                    raise TypeError("all elements must match type %s" % tp)
                keys = list(value.keys())

            if issubclass(raw_value_type, collections.abc.Sequence):
                values = [Field.convert_sequence(value_type, element) for element in value.values()]
            elif issubclass(raw_value_type, collections.abc.Mapping):
                values = [Field.convert_mapping(value_type, element) for element in value.values()]
            else:
                if any(not isinstance(element, raw_value_type) for element in value.values()):
                    raise TypeError("all elements must match type %s" % tp)
                values = list(value.values())

            return {key: value for (key, value) in zip(keys, values)}
        else:
            if not isinstance(value, tp):
                raise TypeError("value does not match type %s" % tp)
            return tp(value)


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
                if not isinstance(field, Field):
                    raise TypeError("Expected a Field instance, got %s" % field)
                new_type.__fields__[name] = getattr(new_type, name)
            else:
                new_type.__fields__[name] = Field(name)
            new_type.__fields__[name].tp = field_type

        for name, value in args[2].items():
            if name.startswith("__") and name.endswith("__"):
                continue

            if callable(value):
                continue

            if not isinstance(value, Field):
                raise TypeError("Expected a Field instance, got %s (%s)" % (value, name))

            if name not in new_type.__fields__:
                new_type.__fields__[name] = value

        return new_type


class Entity(metaclass=EntityMeta):
    __fields__: typing.ClassVar[dict[str, Field]]

    def __init__(self, **kwargs):
        for key, field in self.__fields__.items():
            if key not in kwargs:
                raise ValueError(f"missing value for field '{key}'")

            setattr(self, key, field.convert(kwargs[key]))
            kwargs.pop(key)
            
        if kwargs:
            keys = list(kwargs.keys())
            raise ValueError(f"entity {self.__name__} has no field {keys[0]}")


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
            values[key] = field.convert(values[key])
        return values

