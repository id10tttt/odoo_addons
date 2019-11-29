#!/usr/bin/env bash
mkdir -p ~/celery_log
path=`cd ~/celery_log; pwd`
touch ~/celery_log/aop_receive_from_wms.log
celery multi start w1 -A aop_receive_from_wms --loglevel=info --logfile=$path/aop_receive_from_wms.log --pidfile=$path/w1.pid