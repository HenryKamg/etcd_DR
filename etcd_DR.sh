#!/bin/sh

ROOTPATH=`dirname $0`
LOGFILE="${ROOTPATH}/log/etcdlog_$*_`date +"%Y-%m-%d_%H:%M:%S"`.log"
LOGFILE=`echo $LOGFILE |sed 's/ /_/g'`
BIOSCOM="${ROOTPATH}/bin/etcd"
#sh -x $BIOSCOM -l "$LOGFILE" $*
bash -x $BIOSCOM -l "$LOGFILE" $* 2>$LOGFILE

