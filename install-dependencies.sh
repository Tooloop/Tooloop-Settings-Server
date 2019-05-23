#!/bin/bash

if [ $EUID != 0 ]; then
  echo "This script must be run as root."
  exit $exit_code
    exit 1
fi

apt install -y \
    python-pip \
    python-augeas \
    python-crontab \
    python-pexpect \
    python-apt \
    aptitude

pip install flask
