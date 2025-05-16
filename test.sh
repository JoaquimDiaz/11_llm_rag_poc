#!/bin/bash
set -e

export PYTHONPATH=$(pwd)

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "Virtual environment not found, make sure you create the virtual environment before running."
    exit 1
fi

pytest
