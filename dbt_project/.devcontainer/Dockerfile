FROM python:3.10

#RUN apt-get update && apt-get install -yy zsh python-dev libsasl2-dev libsasl2-modules gcc \
RUN apt-get update && apt-get install -yy zsh libsasl2-dev libsasl2-modules gcc \
    && usermod --shell  $(which zsh) root \
    && pip install pipenv \
	&& apt-get clean 

ENV DBT_PROFILES_DIR=/workspace/.dbt/

ENTRYPOINT [ "/bin/zsh" ]