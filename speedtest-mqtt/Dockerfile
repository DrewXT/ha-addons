ARG BUILD_FROM
FROM ${BUILD_FROM:-ghcr.io/home-assistant/amd64-base:latest}

# Re-declare after FROM so the ARG is in scope for RUN steps
ARG BUILD_FROM

# Install runtime dependencies
RUN apk add --no-cache \
    bash \
    curl \
    jq \
    libstdc++ \
    mosquitto-clients \
    tar

# Install Ookla Speedtest CLI.
# Uses uname -m at build time — avoids relying on BUILD_ARCH which the
# HA Supervisor passes as blank for local/custom add-ons.
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

# Copy rootfs overlay (scripts, s6 service definitions)
COPY rootfs /

# Ensure scripts are executable (defensive — git may not preserve bits)
RUN chmod +x /usr/bin/speedtest_run.sh /usr/bin/speedtest_loop.sh \
             /etc/s6-overlay/s6-rc.d/speedtest/run
