ARG BUILD_FROM
FROM $BUILD_FROM

# Install dependencies
RUN apk add --no-cache \
    bash \
    curl \
    jq \
    libstdc++ \
    mosquitto-clients \
    tar

# Install Ookla Speedtest CLI via direct binary download.
# Maps the Docker/HA build architecture to the Ookla release tarball name.
ARG BUILD_ARCH
RUN set -eux; \
    case "${BUILD_ARCH}" in \
        amd64)   ARCH="x86_64"   ;; \
        aarch64) ARCH="aarch64"  ;; \
        armv7)   ARCH="armhf"    ;; \
        armhf)   ARCH="armel"    ;; \
        *)       echo "Unsupported arch: ${BUILD_ARCH}"; exit 1 ;; \
    esac; \
    URL="https://install.speedtest.net/app/cli/ookla-speedtest-1.2.0-linux-${ARCH}.tgz"; \
    echo "Downloading Speedtest CLI from: ${URL}"; \
    curl -fsSL "${URL}" -o /tmp/speedtest.tgz; \
    tar -xzf /tmp/speedtest.tgz -C /tmp; \
    mv /tmp/speedtest /usr/bin/speedtest; \
    chmod +x /usr/bin/speedtest; \
    rm -rf /tmp/speedtest.tgz /tmp/speedtest.5.*; \
    speedtest --version

# Copy scripts
COPY rootfs /

# Make scripts executable
RUN chmod +x /usr/bin/speedtest_run.sh /usr/bin/speedtest_loop.sh
