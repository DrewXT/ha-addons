ARG BUILD_FROM
FROM ${BUILD_FROM:-ghcr.io/home-assistant/amd64-base:latest}

# Install runtime dependencies
RUN apk add --no-cache \
    bash \
    curl \
    jq \
    libstdc++ \
    mosquitto-clients \
    python3 \
    py3-pip \
    tar

# Install Python MQTT library
RUN pip3 install --no-cache-dir --break-system-packages paho-mqtt

# Install Ookla Speedtest CLI via direct binary download.
# Uses uname -m — avoids relying on BUILD_ARCH which the Supervisor passes blank.
RUN set -eux; \
    UNAME="$(uname -m)"; \
    echo "Detected machine arch: ${UNAME}"; \
    case "${UNAME}" in \
        x86_64)  ARCH="x86_64"  ;; \
        aarch64) ARCH="aarch64" ;; \
        armv7l)  ARCH="armhf"   ;; \
        armv6l)  ARCH="armel"   ;; \
        *)       echo "Unsupported arch: ${UNAME}"; exit 1 ;; \
    esac; \
    URL="https://install.speedtest.net/app/cli/ookla-speedtest-1.2.0-linux-${ARCH}.tgz"; \
    echo "Downloading: ${URL}"; \
    curl -fsSL "${URL}" -o /tmp/speedtest.tgz; \
    tar -xzf /tmp/speedtest.tgz -C /tmp; \
    mv /tmp/speedtest /usr/bin/speedtest; \
    chmod +x /usr/bin/speedtest; \
    rm -rf /tmp/speedtest.tgz /tmp/speedtest.md /tmp/speedtest.5.*; \
    speedtest --version

# Accept the Ookla license at build time so it never prompts at runtime
RUN speedtest --accept-license --accept-gdpr > /dev/null 2>&1 || true

# Copy rootfs overlay
COPY rootfs /

# Ensure scripts are executable
RUN chmod +x /usr/bin/speedtest_mqtt.py \
             /etc/s6-overlay/s6-rc.d/speedtest/run
