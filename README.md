# Djocketry-boiler

Boilerplate for Django-Docker-Poetry projects  
Based on a 2020 [tutorial](https://medium.com/@samwelkanda/how-to-initialize-a-django-project-with-poetry-and-docker-ef4997006f2f) 
by [Samwel Kanda](https://medium.com/@samwelkanda)


# Packages
## External 
Make sure you have compatible versions of these installed

- [Python 3.10.6](https://www.python.org/downloads/release/python-3106/)
- [Poetry 1.1.14](https://python-poetry.org/blog/announcing-poetry-1.1.14/)
- [Docker 20.10.17](https://docs.docker.com/engine/release-notes/#201017)

## Internal 
Docker will handle these, no need to install manually
- [Django 4.1](https://docs.djangoproject.com/en/4.1/releases/4.1/)
- [PostgreSQL 14.4](https://www.postgresql.org/docs/current/release-14-4.html)

# Instructions

## Linux

### Set up 
1. Create project directory and move into it `mkdir <project-name> && cd $_`
2. Clone this repository `git clone git@github.com:fr-mm/djocketry-boiler.git .`
3. Setup project (rename boilerplate mentions) `python setup.py`
4. Build Docker containers images `sudo docker compose build`

### Usage
1. On project's root directory, start Docker containers `sudo docker compose up`
   - To run in background (detached mode) run the previous command with `-d` flag at the end
   - To stop containers running and background `sudo docker compose down` 
2. Application should be running at `localhost:8000`

## Windows
TBD