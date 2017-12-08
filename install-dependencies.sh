#!/bin/bash

if [ $EUID != 0 ]; then
  echo "This script must be run as root."
  exit $exit_code
    exit 1
fi

apt-get install -y \
    python-pip \
    python-augeas \
    python-crontab

pip install flask