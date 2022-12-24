#!/usr/bin/env bash

# Source bash common
source ci/bash_common.sh

# Activate venv
activateVenv

# Run linting
runBlack
successCheck "Black check"
runIsort
successCheck "Isort check"
runFlake8
successCheck "Flake8 check"
runMypy
successCheck "Mypy check"

read -p "CI Checks Passed! Press Enter Key to Complete..."
