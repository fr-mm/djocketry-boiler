from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple


@dataclass(frozen=True)
class Project:
    name: str
    version: str
    description: str
    authors: List[str]

    @classmethod
    def from_input(cls) -> Project:
        print('Enter project info')
        name = cls.__input('Name')
        description = cls.__input('Description')
        authors = cls.__input('Authors')
        return cls(
            name=name,
            version='0.1.0',
            description=description,
            authors=cls.__parse_authors(authors)
        )

    @staticmethod
    def __input(message: str) -> str:
        identation_size = 4
        identation = ' ' * identation_size
        return input(f'{identation}{message}: ').strip()

    @staticmethod
    def __parse_authors(authors: str) -> List[str]:
        if authors[0] == '[' and authors[-1] == ']':
            authors = authors[1:-1]
        return authors.split(',')


@dataclass(frozen=True)
class File:
    path: Path

    @property
    def content(self) -> str:
        with open(self.path, 'r') as file:
            return file.read()

    def replace(self, old: str, new: str) -> None:
        new_content = re.sub(old, new, self.content)
        self.__override(new_content)

    def __override(self, content: str) -> None:
        with open(self.path, 'w') as file:
            file.write(content)


class PyprojectToml:
    __FILE_NAME = 'pyproject.toml'
    __file: File

    def __init__(self) -> None:
        file_path = Path(__file__).parent.joinpath(self.__FILE_NAME)
        self.__file = File(file_path)

    @property
    def file_name(self) -> str:
        return self.__FILE_NAME

    def replace_attributes(self, *attributes: Tuple[str, str] or Tuple[str, List[str]]) -> None:
        [self.replace_attribute(*attribute) for attribute in attributes]

    def replace_attribute(self, key: str, value: str or List[str]) -> None:
        value_type = type(value)
        if value_type is str:
            self.replace_string_attribute(key, value)
        elif value_type is list:
            self.replace_list_attribute(key, value)
        else:
            Exception(f'Unexpected type: {value} is {type(value)}')

    def replace_string_attribute(self, key: str, value: str) -> None:
        pattern = fr'{key} ?= ?".*"'
        substitution = fr'{key} = "{value}"'
        self.__file.replace(pattern, substitution)

    def replace_list_attribute(self, key: str, value: List[str]) -> None:
        formatted_items = [f'"{item.strip()}"' for item in value]
        formatted_value = f'[{", ".join(formatted_items)}]'
        pattern = fr'{key} ?= ?\[.*\]'
        substitution = fr'{key} = {formatted_value}'
        self.__file.replace(pattern, substitution)


class SetUp:
    def execute(self) -> None:
        project = Project.from_input()
        self.__edit_pyproject_toml(project)

    @staticmethod
    def __edit_pyproject_toml(project: Project) -> None:
        pyproject_toml = PyprojectToml()
        pyproject_toml.replace_attributes(
            ('name', project.name),
            ('version', project.version),
            ('description', project.description),
            ('authors', project.authors)
        )
        print(f'{pyproject_toml.file_name} edited')


SetUp().execute()
