# minio-sidecar

## Description

This charm encompasses the Kubernetes operator for MinIO.

The MinIO operator is a Python script that wraps the latest released MinIO, providing
lifecycle management for each application and handling events such as install, upgrade,
integrate, and remove.

## Usage

## Install
To install MinIO, run:

    snap install juju --classic
    snap install microk8s --classic
    microk8s enable dns storage
    juju bootstrap microk8s micro
    juju add-model my-charm-model

    charmcraft build
    juju deploy ./minio-operator.charm --resource minio-image=minio/minio

## Developing

Create and activate a virtualenv with the development requirements:

    virtualenv -p python3 venv
    source venv/bin/activate
    pip install -r requirements-dev.txt

## Testing

The Python operator framework includes a very nice harness for testing
operator behaviour without full deployment. Just `run_tests`:

    ./run_tests
