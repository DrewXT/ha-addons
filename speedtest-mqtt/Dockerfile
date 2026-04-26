ARG BUILD_FROM
FROM $BUILD_FROM

# Install dependencies
RUN apk add --no-cache \
    curl \
    jq \
    mosquitto-clients \
    bash

# Install Speedtest CLI
RUN curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.alpine.sh | bash && \
    apk add --no-cache speedtest

# Copy scripts
COPY rootfs /

# Make scripts executable
RUN chmod +x /usr/bin/speedtest_run.sh /usr/bin/speedtest_loop.sh
