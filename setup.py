from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple


OLD_NAME = 'djocketry-boiler'


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
            name=cls.__parse_name(name),
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
    def __parse_name(name: str) -> str:
        return name.replace(' ', '-')

    @staticmethod
    def __parse_authors(authors: str) -> List[str]:
        if authors[0] == '[' and authors[-1] == ']':
            authors = authors[1:-1]
        return authors.split(',')


class File:
    __path: Path

    def __init__(self, path: str) -> None:
        self.__path = Path(path)

    @property
    def path(self) -> Path:
        return self.__path

    @property
    def name(self) -> str:
        return self.path.name

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


class DefaultFile:
    __new_project_name: str
    __expected_project_name_mentions: int
    __file: File

    def __init__(self, path: str, expected_project_name_mentions: int) -> None:
        self.__file = File(path)
        self.__expected_project_name_mentions = expected_project_name_mentions

    @classmethod
    def set_new_project_name(cls, name: str) -> None:
        cls.__new_project_name = name

    def replace_project_name(self) -> None:
        if self.__replacement_allowed():
            self.__file.replace(old=OLD_NAME, new=self.__new_project_name)
            print(f'{self.__file.name} edited')

    def __replacement_allowed(self) -> bool:
        old_name_mentions = self.__count_old_project_name_mentions()
        if old_name_mentions != self.__expected_project_name_mentions:
            yes, no = 'y', 'n'
            message = f'{self.__file.name} should mention {OLD_NAME} {self.__expected_project_name_mentions} times,\n' \
                      f'but only {old_name_mentions} were found.\n' \
                      f'This can cause issues, edit anyway? ({yes}/{no}) '
            answer = ''
            while answer not in [yes, no]:
                answer = input(message).lower()
            if answer is no:
                return False
        return True

    def __count_old_project_name_mentions(self) -> int:
        return len(re.findall(rf'{OLD_NAME}', self.__file.content))


class PyprojectToml:
    __FILE_NAME = 'pyproject.toml'
    __file: File

    def __init__(self) -> None:
        self.__file = File(self.__FILE_NAME)

    @property
    def file_name(self) -> str:
        return self.__file.name

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
    __project: Project

    def execute(self) -> None:
        self.__project = Project.from_input()
        self.__edit_default_files()
        self.__edit_pyproject_toml()
        self.__rename_directories()

    def __edit_pyproject_toml(self) -> None:
        pyproject_toml = PyprojectToml()
        pyproject_toml.replace_attributes(
            ('name', self.__project.name),
            ('version', self.__project.version),
            ('description', self.__project.description),
            ('authors', self.__project.authors)
        )
        print(f'{pyproject_toml.file_name} edited')

    def __edit_default_files(self) -> None:
        DefaultFile.set_new_project_name(self.__project.name)
        files = [
            DefaultFile(path='manage.py', expected_project_name_mentions=1),
            DefaultFile('docker-compose.yml', 3),
            DefaultFile(f'{OLD_NAME}/asgi.py', 2),
            DefaultFile(f'{OLD_NAME}/settings.py', 3),
            DefaultFile(f'{OLD_NAME}/urls.py', 1),
            DefaultFile(f'{OLD_NAME}/wsgi.py', 2)
        ]
        [file.replace_project_name() for file in files]

    def __rename_directories(self) -> None:
        old_parent = Path(__file__).parent
        new_parent = old_parent.parent.joinpath(self.__project.name)
        os.rename(OLD_NAME, self.__project.name)
        os.rename(old_parent, new_parent)
        os.chdir(new_parent)
        print('Directories renamed')


SetUp().execute()
