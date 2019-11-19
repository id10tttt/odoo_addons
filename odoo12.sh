#!/usr/bin/env bash
# 安装 docker
sudo apt-get remove docker docker-engine docker.io containerd runc
sudo apt-get update && sudo apt-get install \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common -y
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) \
  stable"
sudo apt-get update && sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose -y

sudo usermod -aG docker ${USER}
sudo systemctl restart docker

# 生成文件
mkdir -p ~/odoo12_docker/pgdata
mkdir -p ~/odoo12_docker/share
mkdir -p ~/odoo12_docker/odooconf
mkdir -p ~/odoo12_docker/customer_addons
cd ~/odoo12_docker
touch docker-compose.yml

echo "[options]
addons_path = /usr/lib/python3/dist-packages/odoo/addons,/mnt/odoo
data_dir = /var/lib/odoo/.local/share/Odoo
db_host = db
db_maxconn = 64
db_name = False
db_password = False
db_port = 5432
db_sslmode = prefer
db_template = template0
db_user = odoo
dbfilter =
demo = {}
server_wide_modules = base,web
http_enable = True
http_interface =
http_port = 8069
" > odooconf/odoo.conf

echo "
version: \""3.0\""
services:
  db:
    image:    postgres:12
    volumes:
      - ~/odoo12_docker/pgdata:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=odoo
      - POSTGRESQL_PASSWORD=odoo
      - POSTGRES_DB=postgres
    restart: always

  odoo12:
    image:    1di0t/odooce:12
    depends_on:
      - db
    ports:
      - "8090:8069"
    volumes:
      - ~/odoo12_docker/share:/var/lib/odoo/share
      - ~/odoo12_docker/odooconf:/etc/odoo
      - ~/odoo12_docker/customer_addons:/mnt/odoo
    command: -- --dev=reload
    restart: always

volumes:
  db:
  odoo12:
" > docker-compose.yml
