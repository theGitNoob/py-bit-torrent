#!/bin/bash
ip route add 10.0.10.0/24 via 10.0.11.2 dev eth0
python server.py
tail -f /dev/null