# Katello Certs Tools


## Testing using podman

Make sure you are on a clean checkout

```
podman run --rm -v $(pwd):/app --workdir=/app centos:7 bash ./test.sh
podman run --rm -v $(pwd):/app --workdir=/app centos:8 bash ./test.sh
```
