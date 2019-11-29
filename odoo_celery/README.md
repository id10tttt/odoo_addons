# You should install redis-server and depends first.
    apt update && apt upgrade -y && apt install redis-server -y
    pip3 install zeep celery(pip3 install requirments.txt)

# Start celery
    cd into odoo_celery/celery
    chmod +x *.sh
    ./start_aop_receive_from_wms_celery_worker (You should change name by yourself)