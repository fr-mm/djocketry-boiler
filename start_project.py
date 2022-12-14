from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
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

    @classmethod
    def __parse_name(cls, name: str) -> str:
        name = name.replace(' ', '_')
        name = name.replace('-', '_')
        cls.__validate_name(name)
        return name

    @staticmethod
    def __validate_name(name: str) -> None:
        if not re.match(r'^[a-zA-Z0-9_]*$', name):
            print(f'Invalid name: {name}')
            quit()

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

    def replace_substrings(self, old: str, new: str) -> None:
        new_content = re.sub(old, new, self.content)
        self.override_content(new_content)

    def override_content(self, new_content: str) -> None:
        with open(self.path, 'w') as file:
            file.write(new_content)


class DefaultFile:
    __OLD_PROJECT_NAME = 'djocketry-boiler'
    __new_project_name: str
    __expected_project_name_mentions: int
    __file: File

    def __init__(self, path: str, expected_project_name_mentions: int) -> None:
        self.__file = File(path)
        self.__expected_project_name_mentions = expected_project_name_mentions

    @property
    def name(self) -> str:
        return self.__file.name

    @classmethod
    def set_new_project_name(cls, name: str) -> None:
        cls.__new_project_name = name

    def replace_project_name(self) -> None:
        if self.__replacement_allowed():
            self.__file.replace_substrings(old=self.__OLD_PROJECT_NAME, new=self.__new_project_name)

    def __replacement_allowed(self) -> bool:
        old_name_mentions = self.__count_old_project_name_mentions()
        if old_name_mentions != self.__expected_project_name_mentions:
            yes, no = 'y', 'n'
            message = f'{self.__file.name} should mention {self.__OLD_PROJECT_NAME} {self.__expected_project_name_mentions} times,\n' \
                      f'but only {old_name_mentions} were found.\n' \
                      f'This can cause issues, edit anyway? ({yes}/{no}) '
            answer = ''
            while answer not in [yes, no]:
                answer = input(message).lower()
            if answer is no:
                return False
        return True

    def __count_old_project_name_mentions(self) -> int:
        return len(re.findall(rf'{self.__OLD_PROJECT_NAME}', self.__file.content))


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
        self.__file.replace_substrings(pattern, substitution)

    def replace_list_attribute(self, key: str, value: List[str]) -> None:
        formatted_items = [f'"{item.strip()}"' for item in value]
        formatted_value = f'[{", ".join(formatted_items)}]'
        pattern = fr'{key} ?= ?\[.*\]'
        substitution = fr'{key} = {formatted_value}'
        self.__file.replace_substrings(pattern, substitution)


class SetUp:
    __project: Project

    def execute(self) -> None:
        self.__go_to_root()
        self.__validate_poetry_and_docker()
        self.__project = Project.from_input()
        self.__replace_project_name_in_files()
        self.__install_dependencies()
        self.__start_django_project()
        self.__update_db_in_django_settings()
        self.__delete_git_repository()
        self.__build_and_run_docker_containers()
        self.__delete_this_file()
        print(
            f'Project build and runing\n'
            f'To stop it: docker compose down\n'
            f'To rerun it: docker compose up'
        )

    @staticmethod
    def __go_to_root() -> None:
        os.chdir(Path(__file__).parent)

    def __validate_poetry_and_docker(self) -> None:
        self.__run_command('poetry --version')
        self.__run_command('docker --version')

    def __install_dependencies(self) -> None:
        self.__run_command('poetry install')

    def __start_django_project(self) -> None:
        self.__run_command(f'poetry run django-admin startproject {self.__project.name} .')

    def __update_db_in_django_settings(self) -> None:
        django_settings = File(f'{self.__project.name}/settings.py')
        pattern = r'DATABASES[\w ={\'\"\n:.,()/]*}\n}'
        old_databases = re.search(pattern, django_settings.content).group()
        new_databases = "DATABASES = {\n" \
                        "    'default': {\n" \
                        "        'ENGINE': os.environ.get('SQL_ENGINE'),\n" \
                        "        'NAME': os.environ.get('SQL_DATABASE'),\n" \
                        "        'USER: os.environ.get('SQL_USER'),\n" \
                        "        'PASSWORD: os.environ.get('SQL_PASSWORD'),\n" \
                        "        'HOST': os.environ.get('SQL_HOST'),\n" \
                        "        'PORT': os.environ.get('SQL_PORT')\n" \
                        "    }\n" \
                        "}"
        django_settings.replace_substrings(old_databases, new_databases)

    def __replace_project_name_in_files(self) -> None:
        self.__clear_readme()
        self.__edit_docker_compose()
        self.__edit_pyproject_toml()

    @staticmethod
    def __delete_git_repository() -> None:
        git_repository = '.git'
        if Path(git_repository).exists():
            shutil.rmtree(git_repository, ignore_errors=True)
            print('Git repository deleted')

    @staticmethod
    def __delete_this_file() -> None:
        os.remove(__file__)
        print('start_project stript deleted')

    def __build_and_run_docker_containers(self) -> None:
        prefix = ''
        if sys.platform != 'win32':
            prefix = 'sudo '
        self.__run_command(f'{prefix}docker compose up -d --build')

    @staticmethod
    def __run_command(command: str) -> None:
        process = subprocess.run(command, shell=True)
        if process.returncode != 0:
            print(f'Failed to run command: {command}')
            quit()

    @staticmethod
    def __clear_readme() -> None:
        readme = File('README.md')
        readme.override_content(new_content='')

    def __edit_pyproject_toml(self) -> None:
        pyproject_toml = PyprojectToml()
        pyproject_toml.replace_attributes(
            ('name', self.__project.name),
            ('version', self.__project.version),
            ('description', self.__project.description),
            ('authors', self.__project.authors)
        )
        print(f'pyproject.toml edited')

    def __edit_docker_compose(self) -> None:
        DefaultFile.set_new_project_name(self.__project.name)
        docker_compose = DefaultFile(path='docker-compose.yml', expected_project_name_mentions=3)
        docker_compose.replace_project_name()
        print(f'docker-compose.yml edited')


SetUp().execute()
