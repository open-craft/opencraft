#!/usr/bin/env bash
set -euxo pipefail

rm -f packages/api_client/apis/*.ts
rm -f packages/api_client/models/*.ts

docker run --rm --network="host" -v ${PWD}:/local \
    openapitools/openapi-generator-cli:v4.3.1 generate \
    -i http://localhost:5000/api/swagger/?format=openapi \
    -g typescript-fetch \
    --remove-operation-id-prefix \
    --config /local/packages/api_client/openapi-generator-config.json \
    -o /local/packages/api_client
