#!/usr/bin/env bash
set -euxo pipefail

# All commands should be idempotent.

printf "\n"

API_CLIENT_PATH="packages/api_client"

rm -rf $API_CLIENT_PATH/dist
npm install --prefix=$API_CLIENT_PATH
npm run build --prefix=$API_CLIENT_PATH

printf "API Client build complete."
