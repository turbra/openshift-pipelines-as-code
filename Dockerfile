FROM registry.access.redhat.com/ubi9/python-312:latest

USER root

# Apply package updates during the image build.
RUN dnf -y upgrade --refresh && \
    dnf clean all && \
    rm -rf /var/cache/dnf

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

WORKDIR /opt/app-root/src

# Install Python dependencies first for better layer caching.
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

# Copy the application source.
COPY app ./app

# OpenShift runs with an arbitrary UID in GID 0.
RUN chgrp -R 0 /opt/app-root/src && chmod -R g=u /opt/app-root/src

USER 1001

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
