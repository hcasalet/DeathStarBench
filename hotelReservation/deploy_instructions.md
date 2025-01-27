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

4. Save ssh key in Github
-- generate the public key
  % ssh-keygen -t ed25519 -C "<email>"
-- display key on command line
  % cat ~/.ssh/id_ed25519.pub 
-- add key in Github settings/ssh keys

5. Get the project
  % git clone https://github.com/hcasalet/DeathStarBench.git
  % cd DeathStarBench
  % git submodule update --init --recursive

6. Start docker containers
-- 6.1 start the containers
  % cd DeathStarBench/hotelReservation
  % docker-compose up -d --build
-- or 6.2 start Swarm, on Node 1
  % docker swarm init --advertise-addr <managerIp>  // use eno1
-- then on other worker nodes
  % docker swarm join --token <token> <managerIp>:2377
-- on manager node, build image
  % ./build_exec.sh
  % docker build --no-cache -f Dockerfile.swarm -t hotel-reservation-swarm:latest .
  % docker save -o my-service.tar hotel-reservation-swarm:latest
  % ssh-keygen -t rsa -b 4096
  % cat ~/.ssh/id_rsa.pub
  % manually add from above to worker nodes ~/.ssh/authorized_keys file
  % scp my-service.tar user@workerIp:/path/to/destination
-- on worker nodes:
  % docker load -i my-service.tar
-- on all nodes:
  % sudo nano /etc/docker/daemon.json 
  % add: {
            "dns": ["8.8.8.8", "8.8.4.4"]
         } in the file
  % sudo systemctl restart docker
  % check: docker run --rm busybox cat /etc/resolv.conf

-- on manager node:
  % docker stack deploy -c docker-compose.yml hotel-reservation

-- docker operational commands:
-- cleaning up stack deploy
  % docker stack rm <deploy-name>  // for ex, hotel-reservation is the deploy name
  % docker stack ls    // check if stack still exists
  % docker service ls    // check if any services are running
  % docker ps -a         // check if any containers are up
  % docker system prune -f     // release resources used
-- debugging
  % docker service ps <service-name>
  % docker inspect <task-id>
  % docker network inspect <overlay-network-name>
  % docker run -it --rm <image-name> sh  (dummy container to debug)


6. Build workload generator
  % cd wrk2   // from DeathStarBench root
  % git submodule update --init --recursive
  % sudo apt-get update
  % sudo apt install openssl libssl-dev libz-dev
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
