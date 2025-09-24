FROM python:slim

WORKDIR /usr/src/app
COPY . .
RUN uv venv && uv pip install -e .

CMD [ "uv", "run", "sandbox-server" ]
