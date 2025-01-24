#!/bin/sh
cd src
timeout --kill-after=1s 10m python3 -u ./pot.py --rounds 3