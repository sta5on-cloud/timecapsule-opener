#!/bin/sh
# Build function.zip for the python3.12 Lambda runtime (pg8000 is pure Python, so this works on any OS).
set -e
cd "$(dirname "$0")"
rm -rf build function.zip
python3 -m pip install --disable-pip-version-check --quiet --target build -r requirements.txt
cp lambda_function.py rds-ca.pem build/
(cd build && zip -qr ../function.zip .)
ls -l function.zip
