from .entity import Entity, Field


class TerminalColors(Entity):
    foreground: str = Field(default="white")
    background: str = Field(default="black")

    contrast: str = Field(default="#777777")
    error: str    = Field(default="#FF746C")


class Settings(Entity):
    colors: TerminalColors = Field(default=TerminalColors())

