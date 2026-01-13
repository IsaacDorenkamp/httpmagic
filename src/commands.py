from __future__ import annotations
import enum
import io
import itertools
import typing

import logging


class CommandError(Exception):
    pass


__registry = {}

def register(command, args: list[str] | None = None):
    def decorator(fn):
        __registry[command] = fn, (args or [])
        return fn
    return decorator


class ParseState(enum.Enum):
    expecting = 0
    argument = 1
    double_quotes = 2
    single_quotes = 3


def parse_arguments(raw_arguments: str, argument_definition: list[str]):
    # first, parse argument list
    arguments: list[str] = []
    argument = io.StringIO()
    state = ParseState.expecting
    for ch in raw_arguments:
        match state:
            case ParseState.expecting:
                if ch == '"':
                    state = ParseState.double_quotes
                elif ch == "'":
                    state = ParseState.single_quotes
                elif ch.isspace():
                    continue
                else:
                    state = ParseState.argument
                    argument.write(ch)
            case ParseState.argument:
                if ch.isspace():
                    state = ParseState.expecting
                    logging.debug("argument: %s" % argument.getvalue())
                    arguments.append(argument.getvalue())
                    argument = io.StringIO()
                elif ch == '"':
                    state = ParseState.double_quotes
                    arguments.append(argument.getvalue())
                    argument = io.StringIO()
                elif ch == "'":
                    state = ParseState.single_quotes
                    argument.append(argument.getvalue())
                    argument = io.StringIO()
                else:
                    argument.write(ch)
            case ParseState.double_quotes:
                if ch == '"':
                    state = ParseState.expecting
                    arguments.append(argument.getvalue())
                    argument = io.StringIO()
                else:
                    argument.write(ch)
            case ParseState.single_quotes:
                if ch == "'":
                    state = ParseState.expecting
                    arguments.append(argument.getvalue())
                    argument = io.StringIO()
                else:
                    argument.write(ch)

    if state in (ParseState.double_quotes, ParseState.single_quotes):
        raise CommandError("Missing closing quote!")
    elif state == ParseState.argument:
        arguments.append(argument.getvalue())

    logging.debug("arguments: %s" % str(arguments))

    parsed_arguments = {}
    for raw_arg_name, arg_value in itertools.zip_longest(argument_definition, arguments):
        if raw_arg_name is None:
            raise CommandError("too many arguments!")
        parts = raw_arg_name.split(":", maxsplit=2)
        arg_name = parts[0]
        if len(parts) == 2:
            tags = parts[1].split(",")
        else:
            tags = []

        if arg_value is None:
            # if arg_value is None, then we have exhausted arguments
            if "optional" in tags:
                break
            else:
                raise CommandError("'%s' is not optional" % arg_name)
        parsed_arguments[arg_name] = arg_value

    return parsed_arguments


def execute(raw_command: str, host: App):
    raw_command = raw_command[1:]  # strip '!'
    parts = raw_command.split(" ", maxsplit=1)
    command = parts[0]
    
    entry = __registry.get(command)
    if entry:
        fn, args = entry
        if len(parts) == 2:
            arguments = parse_arguments(parts[1], args)
        else:
            arguments = parse_arguments("", args)
        fn(arguments, host)
    else:
        raise CommandError("unknown command '%s'" % command)


# built in commands
@register("nr", ["name"])
def command_new_request(args: dict[str, str], app: App):
    name = args["name"]
    app.create_request(name, True)

@register("nc", ["name"])
def command_new_collection(args: dict[str, str], app: App):
    name = args["name"]
    app.create_collection(name, True)


@register("exit", [])
def command_exit(_, app: App):
    app.quit()


if typing.TYPE_CHECKING:
    from app import App

