#!/bin/bash

# List of Docker image tags to delete
tags=(
    "b8f290f6071b"
    "b4f6f4f4980c"
    "30a227b04663"
    "58d8ab53a5f7"
    "876bff5aab70"
    "dee66d39fda2"
    "8bdc24d939c3"
    "c1563a1483d2"
    "8d0cd37756fa"
    "a7278f1f78ab"
    "fd7232f51afc"
    "8cf6ec4a82a9"
    "50a9588f8cbc"
    "d5c68744fd9c"
    "e7d9d2fff54c"
    "8eabbf3dfa67"
)

# Loop through the tags and delete each one
for tag in "${tags[@]}"; do
  echo "Deleting image tag: $tag"
  docker rmi $tag
done