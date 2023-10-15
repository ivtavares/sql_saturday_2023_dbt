FROM python:3.10.13-slim-bookworm


COPY .dbt /.dbt
COPY jaffle_shop /app/jaffle_shop
COPY Pipfile /app/Pipfile
COPY Pipfile.lock /app/Pipfile.lock

ENV DBT_PROFILES_DIR=/.dbt/
WORKDIR /app

RUN  apt-get update && apt-get install \
     && pip install pipenv \
	&& pipenv install --system \
     && apt-get clean

EXPOSE 5000

WORKDIR /app/jaffle_shop
CMD ["flask", "run", "--host=0.0.0.0"]   