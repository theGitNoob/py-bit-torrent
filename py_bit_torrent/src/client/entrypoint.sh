#!/bin/bash
ip route add 10.0.11.0/24 via 10.0.10.2 dev eth0
python client.py
tail -f /dev/null