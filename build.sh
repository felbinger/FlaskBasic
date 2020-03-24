#!/usr/bin/env bash

base_dockerfile="base.Dockerfile"
dockerfile="Dockerfile"
base_image="flaskbasic_base"
image="flaskbasic"

docker=$(which docker)

${docker} build -f "${base_dockerfile}" -t ${base_image} .
${docker} build -f "${dockerfile}" -t ${image} --build-arg "BASE_IMG=${base_image}" .
