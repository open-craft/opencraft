#!/usr/bin/env bash
set -euxo pipefail

# All commands should be idempotent.

printf "\n"

cd packages/api_client
rm -rf dist
npm install
npm run build
cd ../..

printf "\API Client build complete.\n"
