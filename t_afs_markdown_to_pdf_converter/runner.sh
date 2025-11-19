#!/bin/bash

# Update Python packages
pip install --upgrade --force-reinstall pip==25.3 setuptools==78.1.1 urllib3==2.5.0 requests==2.32.4

# Update package list and upgrade fixable Debian packages
apt-get update && apt-get upgrade -y --no-install-recommends \
    libc-bin \
    libc6 \
    libgnutls30 \
    libsqlite3-0 \
    libssl3 \
    openssl \
    perl-base \
    libgssapi-krb5-2 \
    libk5crypto3 \
    libkrb5-3 \
    libkrb5support0 \
    libcap2 \
    libudev1 \
    login \
    passwd \
    gcc-12-base \
    libgcc-s1 \
    libstdc++6 \
    libgdk-pixbuf-2.0-0 \
    libxml2 \
    libxslt1.1 \
    libpam-modules \
    libpam-modules-bin \
    libpam-runtime \
    libpam0g

# Clean up
apt-get clean && rm -rf /var/lib/apt/lists/*