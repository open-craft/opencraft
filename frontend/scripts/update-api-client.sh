#!/usr/bin/env bash
set -euxo pipefail

rm -f packages/api_client/src/apis/*.ts
rm -f packages/api_client/src/models/*.ts

docker run --rm --network="host" -v ${PWD}:/local \
    openapitools/openapi-generator-cli:v5.1.1 generate \
    -i http://localhost:5000/api/swagger/?format=openapi \
    -g typescript-fetch \
    --remove-operation-id-prefix \
    --config /local/packages/api_client/openapi-generator-config.json \
    -o /local/packages/api_client
