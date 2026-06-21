docker network create regress-sheild-net
sudo docker run -it -p 3306:3306 --restart=always --privileged=true --network regress-sheild-net --name RegressSheildMysql -v /Users/test/Desktop/mysql/conf.d:/etc/mysql/conf.d -v /Users/test/Desktop/mysql/logs:/var/log/mysql -v /Users/test/Desktop/mysql/data:/var/lib/mysql -e MYSQL_ROOT_PASSWORD=P@ss1234 mysql:latest

docker run -d --network regress-sheild-net  --restart=always --privileged=true -v /Users/test/Desktop/jenkins-master:/var/jenkins_home -p 50000:50000 -p 8088:8080 --name jenkins-master-regress-sheild jenkins/jenkins


sudo docker run -d --network regress-sheild-net  --restart=always --privileged=true -v /workspace/tonyw/docker/jenkins-master:/var/jenkins_home -p 50000:50000 -p 8088:8080 --name jenkins-master-regress-sheild jenkins/jenkins
sudo docker run -d -p 3306:3306 --restart=always --privileged=true --network regress-sheild-net --name RegressSheildMysql -v /workspace/tonyw/docker/mysql/conf.d:/etc/mysql/conf.d -v /workspace/tonyw/docker/mysql/logs:/var/log/mysql -v /workspace/tonyw/docker/mysql/data:/var/lib/mysql -e MYSQL_ROOT_PASSWORD=P@ss1234 mysql:latest





docker
docker update --restart=always containID


System.setProperty("hudson.model.DirectoryBrowserSupport.CSP", "")




docker run -it -p 3306:3306 --restart=always --privileged=true --network regress-sheild-net --name RegressSheildMysql -v /home/ubuntu/Docker/mysql/conf.d:/etc/mysql/conf.d -v /home/ubuntu/Docker/mysql/logs:/var/log/mysql -v /home/ubuntu/Docker/mysql/data:/var/lib/mysql -e MYSQL_ROOT_PASSWORD=P@ss1234 mysql:latest


docker run -d --network regress-sheild-net  --restart=always --privileged=true -v /home/wrs-ubuntu/workspace/Docker/jenkins-master:/var/jenkins_home -p 50000:50000 -p 8088:8080 --name jenkins-master-regress-sheild jenkins/jenkins

docker run -d -p 3306:3306 --restart=always --privileged=true --network regress-sheild-net --name RegressSheildMysql -v /home/wrs-ubuntu/workspace/Docker/mysql/conf.d:/etc/mysql/conf.d -v /home/wrs-ubuntu/workspace/Docker/mysql/logs:/var/log/mysql -v /home/wrs-ubuntu/workspace/Docker/mysql/data:/var/lib/mysql -e MYSQL_ROOT_PASSWORD=P@ss1234 mysql:latest


