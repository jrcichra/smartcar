#!/bin/bash
sudo apt purge -y docker-ce
export DOCKER_CLI_EXPERIMENTAL=enabled
curl -fsSL https://get.docker.com/ -o docker-install.sh
CHANNEL=nightly sh docker-install.sh
export DOCKER_CLI_EXPERIMENTAL=enabled
docker version
sudo curl -L "https://github.com/docker/compose/releases/download/1.24.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
docker-compose --version
docker buildx --help
docker run --rm --privileged docker/binfmt:820fdd95a9972a5308930a2bdfb8573dd4447ad3
cat /proc/sys/fs/binfmt_misc/qemu-aarch64
docker buildx create --name testbuilder
docker buildx use testbuilder
docker buildx inspect --bootstrap
# Phase 2 - sign in
echo "$DOCKER_PASSWORD" | docker login --username "$DOCKER_USERNAME" --password-stdin 
# Phase 3 - build a container based on the arg passed in
cd containers

if [ "$1" == "rpi" ];then
    for d in */; do
        cd $d
        dir=${d%/}
        docker buildx build --build-arg commit=$GITHUB_SHA -t jrcichra/smartcar_${dir}_rpi --cache-from jrcichra/smartcar_${dir}_rpi -f Dockerfile-rpi --push .
        docker buildx imagetools inspect jrcichra/smartcar_${dir}_rpi
        cd ..
    done
else
    for d in */; do
        cd $d
        dir=${d%/}
        docker buildx build --build-arg commit=$GITHUB_SHA --cache-from jrcichra/smartcar_${dir} --platform linux/amd64,linux/arm64,linux/arm/v7 -t jrcichra/smartcar_${dir} --push .
        docker buildx imagetools inspect jrcichra/smartcar_${dir}
        cd ..
    done
fi