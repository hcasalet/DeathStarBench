# Deploying instructions:
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
- move /var/lib/docker to more capacity
  % systemctl stop docker
  % sudo mkdir /holly/docker
  % sudo chown -R 710 /holly/docker
  % sudo mv /var/lib/docker /holly/
  % sudo ln -s /holly/docker /var/lib/docker
  % sudo systemctl start docker

2. Install Docker compose
 - download software to place in /usr/local/bin<br>
   % sudo curl -L "https://github.com/docker/compose/releases/download/v2.29.1/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose<br>
 - set permission<br>
  % sudo chmod +x /usr/local/bin/docker-compose<br>
 - verify that docker-compose is installed successfully<br>
   % rehash (tcsh may cache executable locations)<br>
   % docker-compose --version<br>
 - Exit and log back in for docker permission to take effect<br>
   % groups<br>

3. Get Go 1.22
 - check go version<br>
   % go version<br>
 - remove go if it is < 1.22<br>
   % sudo rm -rf /usr/local/go<br>
 - download go 1.22<br>
   % wget https://dl.google.com/go/go1.22.4.linux-amd64.tar.gz<br>
 - extract files to usr/local<br>
   % sudo tar -xvf go1.22.4.linux-amd64.tar.gz -C /usr/local<br>
 - add go into path<br>
   % echo "export PATH=\$PATH:/usr/local/go/bin" >> ~/.bashrc<br>
   % echo 'setenv PATH ${PATH}:/usr/local/go/bin' >> ~/.cshrc<br>
 - source .bashrc<br>
   % source ~/.bashrc<br>
   % source ~/.cshrc<br>
 - check to verify go version<br>
   % go version<br>

4. Install python3.11
 - install python3.11 <br>
   % sudo apt update <br>
   % sudo apt install software-properties-common -y <br>
   % sudo add-apt-repository ppa:deadsnakes/ppa <br>
   % sudo apt update <br>
   % sudo apt install python3.11 -y <br>
   % echo 'setenv PATH ${PATH}:/usr/bin/python3.11' <br>
   % sudo apt install python3.11-venv python3.11-distutils -y <br>
   % curl -O https://bootstrap.pypa.io/get-pip.py <br>
   % python3.11 get-pip.py <br>
   % python3.11 -m pip --version <br>
   % python3.11 -m pip install numpy matplotlib <br>

4. Save ssh key in Github
  - generate the public key<br>
   % ssh-keygen -t ed25519 -C "<email>"<br>
  - display key on command line<br>
   % cat ~/.ssh/id_ed25519.pub<br>
  - add key in Github settings/ssh keys<br>

5. Get the project
  % git clone git@github.com:hcasalet/DeathStarBench.git<br>
  % cd DeathStarBench<br>
  % git submodule update --init --recursive<br>

6. Start docker containers
  - 6.1 start the containers<br>
   % cd DeathStarBench/hotelReservation<br>
   % docker-compose up -d --build<br>
 - or 6.2 start Swarm, on Node 1<br>
   % docker swarm init --advertise-addr <managerIp>  // use eno1<br>
 - then on other worker nodes<br>
   % docker swarm join --token <token> <managerIp>:2377<br>
 - on manager node, build image<br>
   % ./build_exec.sh<br>
   % docker build --no-cache -f Dockerfile.swarm -t hotel-reservation-swarm:latest . <br>
   % docker save -o my-service.tar hotel-reservation-swarm:latest<br>
   % ssh-keygen -t rsa -b 4096<br>
   % cat ~/.ssh/id_rsa.pub<br>
   % manually add from above to worker nodes ~/.ssh/authorized_keys file<br>
   % scp my-service.tar user@workerIp:/path/to/destination<br>
 - on worker nodes:<br>
   % docker load -i my-service.tar<br>
 - on all nodes:<br>
   % sudo nano /etc/docker/daemon.json <br>
   % add: {<br>
            "dns": ["8.8.8.8", "8.8.4.4"]<br>
          } in the file<br>
   % sudo systemctl restart docker<br>
   % check: docker run --rm busybox cat /etc/resolv.conf<br>

 - on manager node:<br>
   % docker stack deploy -c docker-compose-swarm.yml hotel-reservation<br>

 - docker operational commands:<br>
 - cleaning up stack deploy<br>
   % docker stack rm <deploy-name>  // for ex, hotel-reservation is the deploy name<br>
   % docker stack ls    // check if stack still exists<br>
   % docker service ls    // check if any services are running<br>
   % docker ps -a         // check if any containers are up<br>
   % docker system prune -f     // release resources used<br>
 - debugging<br>
   % docker service ps <service-name><br>
   % docker inspect <task-id><br>
   % docker network inspect <overlay-network-name><br>
   % docker run -it --rm <image-name> sh  (dummy container to debug)<br>


6. Build workload generator
   % cd wrk2   // from DeathStarBench root<br>
   % git submodule update --init --recursive<br>
   % sudo apt-get update<br>
   % sudo apt install openssl libssl-dev libz-dev<br>
   % sudo apt-get install luarocks<br>
   % sudo luarocks install luasocket<br>
   % make
6.1 For socialNetwork:
   % sudo apt-get install python3-pip<br>
   % pip3 install aiohttp<br>
   % sudo luarocks install luasocket<br>
   % sudo apt-get install libssl-dev libz-dev<br>

7. Run the workload
   % ../wrk2/wrk -D exp -t20 -c1000 -d300s -L -s ./wrk2/scripts/hotel-reservation/mixed-workload_type_1.lua http://127.0.0.1:5000 -R1000
