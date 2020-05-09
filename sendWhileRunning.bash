#/bin/bash



source ftpserver.conf


if [ -z "$1" ]; then
    echo "We need the directory name for the ftp server"
    echo "(not the full path)"
    echo "plz don't use the space character in the name, it's"
    echo "against my religion"
    exit -1
fi

export dirName="$1"

mkdir -p /dev/shm/complete
cd /dev/shm/complete

function sendAndDelete(){
    if [ "$1" == "*.tif" ]; then
	#echo no files, sleeping 1 sec
	sleep 1
    else
        ncftpput -V -u $ftpuser -p $ftppassword $ftpserver ${ftppathprefix}${dirName} $@ && rm -f $@
	echo "ncftpput and rm operation returned $? for $@"
    fi
}

while [ -f "/dev/shm/transferInProgress.flag" ]; do
    sendAndDelete *.tif
done
