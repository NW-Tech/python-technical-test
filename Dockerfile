FROM python:3.10-alpine as build
COPY ./requirements.txt /requirements.txt
RUN python -m venv /pyvenv && \
    /pyvenv/bin/pip install --upgrade pip && \
    /pyvenv/bin/pip install -r requirements.txt

FROM python:3.10-alpine
COPY ./app /app
COPY --from=build /pyvenv /pyvenv
WORKDIR /app
RUN adduser --disabled-password appuser
USER appuser
ENV PATH="/pyvenv/bin:$PATH"
