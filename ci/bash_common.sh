#!/usr/bin/env bash

PYTHON_VERSION='3.10.2'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
DATE_BIN=$(command -v date)
MAKE_BIN=$(command -v make)

successCheck() {
  if [ $? -eq 0 ];
  then
    echo -e "${GREEN}[SUCCESS `${DATE_BIN} +%m-%d-%Y-%H:%M:%S`] ${1} succeeded${NC}"
  else
    echo -e "${RED}[ERROR `${DATE_BIN} +%m-%d-%Y-%H:%M:%S`] ${1} failed${NC}"
    read -p "Press Enter Key to Exit..."
    exit -1
  fi
}

activateVenv() {
  # Activate venv
  if [ $OSTYPE == 'msys' ];
  then
    cd .venv/Scripts && . activate && cd ../../
  else
    source .venv/bin/activate
  fi
  successCheck "Virtual environment activation"
}

runBlack() {
  black src/ --check --diff
}

runIsort() {
  isort src/ --check --diff
}

runFlake8() {
  flake8 src/
}

runMypy() {
  mypy src/
}
