#!/usr/bin/env bash 
set -x


# RUN git submodule update --init --recursive from root

# DOCKER
sudo apt update
sudo apt install apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"
sudo apt update
sudo apt install docker-ce
sudo usermod -aG docker ${USER}
systemctl status docker

# DOCKER-COMPOSE
sudo curl -L "https://github.com/docker/compose/releases/download/v2.29.1/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
rehash
docker-compose --version
groups

# GO

go version
sudo rm -rf /usr/local/go
wget https://dl.google.com/go/go1.22.4.linux-amd64.tar.gz
sudo tar -xvf go1.22.4.linux-amd64.tar.gz -C /usr/local
echo "export PATH=\$PATH:/usr/local/go/bin" >> ~/.bashrc
source ~/.bashrc
go version


# WRK BUILD

cd ../wrk2
git submodule update --init --recursive
sudo apt-get update
sudo apt install openssl libssl-dev libz-dev
sudo apt-get install luarocks
sudo luarocks install luasocket
sudo make
cd ../hotelReservation

