FROM alpine:latest

RUN apk update && apk add --no-cache \
    curl \
    unzip \
    bash \
    jq \
    ca-certificates \
    && rm -rf /var/cache/apk/*

RUN mkdir -p /usr/local/xray && \
    XRAY_VERSION=$(curl -s https://api.github.com/repos/XTLS/Xray-core/releases/latest | jq -r '.tag_name') && \
    echo "Downloading Xray ${XRAY_VERSION}..." && \
    curl -L "https://github.com/XTLS/Xray-core/releases/download/${XRAY_VERSION}/Xray-linux-64.zip" -o /tmp/xray.zip && \
    unzip /tmp/xray.zip -d /usr/local/xray && \
    rm /tmp/xray.zip && \
    chmod +x /usr/local/xray/xray

WORKDIR /usr/local/xray

COPY config.json /usr/local/xray/config.json
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080

CMD ["/entrypoint.sh"]
