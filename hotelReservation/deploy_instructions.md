Deploying instructions:
1. Install Docker
- update the existing package
  % sudo apt update
- install https
  % sudo apt install apt-transport-https ca-certificates curl software-properties-common
- add gpg key for Docker repo in Ubuntu
  % curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
- add Docker repo to apt-source
  % sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"
- add Docker software
  % sudo apt update
  % sudo apt install docker-ce
- add username to Docker group
  % sudo usermod -aG docker ${USER}
- verify docker status
  % systemctl status docker

2. Install Docker compose
- download software to place in /usr/local/bin
  % sudo curl -L "https://github.com/docker/compose/releases/download/v2.29.1/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose
- set permission
  % sudo chmod +x /usr/local/bin/docker-compose
- verify that docker-compose is installed successfully
  % rehash (tcsh may cache executable locations)
  % docker-compose --version
-- Exit and log back in for docker permission to take effect
  % groups

3. Get Go 1.22
-- check go version
  % go version
-- remove go if it is < 1.22
  % sudo rm -rf /usr/local/go
-- download go 1.22
  % wget https://dl.google.com/go/go1.22.4.linux-amd64.tar.gz
-- extract files to usr/local
  % sudo tar -xvf go1.22.4.linux-amd64.tar.gz -C /usr/local
-- add go into path
  % echo "export PATH=\$PATH:/usr/local/go/bin" >> ~/.bashrc
-- source .bashrc
  % source ~/.bashrc
-- check to verify go version
  % go version

4. Get the project
  % git clone https://github.com/hcasalet/DeathStarBench.git
  % cd DeathStarBench
  % git submodule update --init --recursive

5. Start docker containers
-- start the containers
  % cd DeathStarBench/hotelReservation
  % docker-compose up -d --build

6. Build workload generator
  % cd wrk2   // from DeathStarBench root
  % git submodule update --init --recursive
  % sudo apt-get update
  % sudo apt-get install luarocks
  % sudo luarocks install luasocket
  % make
6.1 For socialNetwork:
  % sudo apt-get install python3-pip
  % pip3 install aiohttp
  % sudo luarocks install luasocket
  % sudo apt-get install libssl-dev libz-dev

7. Run the workload
  % ../wrk2/wrk -D exp -t20 -c1000 -d300s -L -s ./wrk2/scripts/hotel-reservation/mixed-workload_type_1.lua http://127.0.0.1:5000 -R1000
