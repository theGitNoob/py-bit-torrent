sysctl -w net.ipv4.ip_forward=1

iptables -P FORWARD ACCEPT

tail -f /dev/null
