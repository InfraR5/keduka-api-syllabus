#!/bin/bash
set -e

# Login to ECR
aws ecr get-login-password --region us-east-1 --profile r5-sso | docker login --username AWS --password-stdin 675705320947.dkr.ecr.us-east-1.amazonaws.com

# Build and Push (AMD64 for Fargate)
docker build --platform linux/amd64 -t keduka-api-syllabus .
docker tag keduka-api-syllabus:latest 675705320947.dkr.ecr.us-east-1.amazonaws.com/keduka-api-syllabus:latest
docker push 675705320947.dkr.ecr.us-east-1.amazonaws.com/keduka-api-syllabus:latest

echo "Deployment image pushed successfully."
