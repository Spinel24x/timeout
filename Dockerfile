FROM python:3.11-alpine

RUN apk update && apk add --no-cache \
    curl \
    unzip \
    bash \
    jq \
    ca-certificates \
    procps \
    && rm -rf /var/cache/apk/*

RUN mkdir -p /usr/local/xray && \
    XRAY_VERSION=$(curl -s https://api.github.com/repos/XTLS/Xray-core/releases/latest | jq -r '.tag_name') && \
    curl -L "https://github.com/XTLS/Xray-core/releases/download/${XRAY_VERSION}/Xray-linux-64.zip" -o /tmp/xray.zip && \
    unzip /tmp/xray.zip -d /usr/local/xray && \
    rm /tmp/xray.zip && \
    chmod +x /usr/local/xray/xray

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY config.json /usr/local/xray/config.json
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080
EXPOSE 10000

CMD ["/entrypoint.sh"]
