FROM python:3.12-slim

ENV PIP_NO_CACHE_DIR=false

RUN apt update && apt install -y libraqm* psutils

WORKDIR /app

COPY . .

RUN pip install -U pip wheel setuptools
RUN pip install poetry poetry-plugin-export

RUN poetry export --without-hashes > requirements.txt
RUN pip uninstall poetry -y
RUN pip install -Ur requirements.txt
RUN pip install . --no-deps

ENTRYPOINT ["python3", "-m", "mr_robot"]
