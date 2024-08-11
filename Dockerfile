FROM python:3.12.4-slim-bullseye

WORKDIR /home

# Copy requirements first for better caching
COPY ./requirements.txt .


RUN python3 -m pip install -r requirements.txt && \
    apt-get clean && \
    apt-get autoclean && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 8000


COPY ./entrypoint.sh .
COPY ./chatApp ./chatApp

# Set permissions for entrypoint
RUN chmod +x entrypoint.sh

CMD ["./entrypoint.sh"]
