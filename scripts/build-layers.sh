#!/bin/bash

# Build Lambda Layers for Scientific Computing and DeepXDE
set -e

# Configuration
PROJECT_NAME="pinn-deepxde-platform"
REGION="us-east-1"
BUCKET_NAME="${PROJECT_NAME}-prod-models"

echo "Building Lambda Layers..."

# Create temporary directory
TEMP_DIR=$(mktemp -d)
echo "Using temporary directory: ${TEMP_DIR}"

# Build Scientific Computing Layer
echo "Building Scientific Computing Layer..."
SCIENTIFIC_DIR="${TEMP_DIR}/scientific-computing"
mkdir -p ${SCIENTIFIC_DIR}/python

# Install scientific computing packages
pip install \
    numpy==1.24.3 \
    scipy==1.11.4 \
    matplotlib==3.8.2 \
    pandas==2.1.4 \
    scikit-learn==1.3.2 \
    -t ${SCIENTIFIC_DIR}/python

# Create zip file
cd ${SCIENTIFIC_DIR}
zip -r ../scientific-computing.zip .
cd -

# Build DeepXDE Layer
echo "Building DeepXDE Layer..."
DEEPXDE_DIR="${TEMP_DIR}/deepxde"
mkdir -p ${DEEPXDE_DIR}/python

# Install DeepXDE and TensorFlow
pip install \
    tensorflow==2.13.0 \
    deepxde==1.10.0 \
    -t ${DEEPXDE_DIR}/python

# Create zip file
cd ${DEEPXDE_DIR}
zip -r ../deepxde.zip .
cd -

# Upload layers to S3
echo "Uploading layers to S3..."

# Check if bucket exists
if ! aws s3 ls "s3://${BUCKET_NAME}" 2>/dev/null; then
    echo "Creating S3 bucket: ${BUCKET_NAME}"
    aws s3 mb "s3://${BUCKET_NAME}" --region ${REGION}
fi

# Upload scientific computing layer
aws s3 cp ${TEMP_DIR}/scientific-computing.zip s3://${BUCKET_NAME}/layers/scientific-computing.zip

# Upload DeepXDE layer
aws s3 cp ${TEMP_DIR}/deepxde.zip s3://${BUCKET_NAME}/layers/deepxde.zip

echo "Layers uploaded to S3"

# Clean up
rm -rf ${TEMP_DIR}

echo "Lambda layers built and uploaded successfully!"
echo "Scientific Computing Layer: s3://${BUCKET_NAME}/layers/scientific-computing.zip"
echo "DeepXDE Layer: s3://${BUCKET_NAME}/layers/deepxde.zip"