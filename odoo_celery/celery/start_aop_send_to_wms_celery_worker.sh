#!/usr/bin/env bash
mkdir -p ~/celery_log
path=`cd ~/celery_log; pwd`
touch ~/celery_log/aop_send_to_wms.log
celery multi start w2 -A aop_send_to_wms --loglevel=info --logfile=$path/aop_send_to_wms.log --pidfile=$path/w2.pid