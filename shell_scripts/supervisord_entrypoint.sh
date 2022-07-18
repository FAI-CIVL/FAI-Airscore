#!/usr/bin/env sh
set -e

#npm run build
#
#if [ $# -eq 0 ] || [ "${1#-}" != "$1" ]; then
#  set -- supervisord "$@"
#fi
#
###############
## SSH setup ##
##

mkdir -p /app/data/ssh/etc /app/data/ssh/run
cp /etc/ssh/sshd_config /app/data/ssh/etc/
echo "Port 1220" >> /app/data/ssh/etc/sshd_config
echo "HostKey /app/data/ssh/etc/ssh_host_rsa_key" >> /app/data/ssh/etc/sshd_config
echo "PidFile /app/data/ssh/sshd.pid" >> /app/data/ssh/etc/sshd_config
echo "AuthorizedKeysFile /app/data/ssh/authorized_keys" >> /app/data/ssh/etc/sshd_config
echo "PrintMotd no" >> /app/data/ssh/etc/sshd_config
echo "PrintLastLog no" >> /app/data/ssh/etc/sshd_config

if [ ! -f /app/data/ssh/etc/ssh_host_rsa_key ]; then
    ssh-keygen -t rsa -f /app/data/ssh/etc/ssh_host_rsa_key  -N ''
fi

### and start sshd
/usr/sbin/sshd -p1220 -f /app/data/ssh/etc/sshd_config -D -e &

exec "$@"
