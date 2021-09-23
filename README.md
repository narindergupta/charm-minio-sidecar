# minio-sidecar

## Description

This charm encompasses the Kubernetes operator for MinIO.

The MinIO operator is a Python script that wraps the latest released MinIO, providing
lifecycle management for each application and handling events such as install, upgrade,
integrate, and remove.

## Usage

## Install
To install MinIO, run:

    lxd init --auto
    snap install juju --classic
    snap install microk8s --classic
    microk8s enable dns storage

    charmcraft pack
    juju bootstrap microk8s micro
    juju add-model minio-demo

    charmcraft build
    juju deploy ./minio_ubuntu-20.04-amd64.charm --resource minio-image=minio/minio

## Debugging
    juju show-status-log minio/0
    juju debug-log --include minio/0

## Developing

Create and activate a virtualenv with the development requirements:

    virtualenv -p python3 venv
    source venv/bin/activate
    pip install -r requirements-dev.txt

## Testing

The Python operator framework includes a very nice harness for testing
operator behaviour without full deployment. Just `run_tests`:

    ./run_tests
