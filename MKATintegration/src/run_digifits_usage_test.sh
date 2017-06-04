#! /bin/bash

export LC_NUMERIC=C

for i in `seq 1 1 5`
do
    echo "python make_fbfobs_sb.py -o ruby --target 'J0437-4715' --backend digifits --duration 60 --backend digifits --backend-args '-t 0.0001531 -p 1' --description='Power detected search mode single pol'"

    echo "python make_fbfobs_sb.py -o ruby --target 'J0437-4715' --backend digifits --duration 60 --backend digifits --backend-args '-t 0.0001531 -p 4' --description='Semi-stokes search mode four pol'"

    echo "python make_fbfobs_sb.py -o ruby --target 'radec, 04:08:20.38, -65:45:09.1' --bw 428 --backend digifits --duration 300 --backend digifits --backend-args '-t 0.000153 -p 4' --drift-scan --description='AR1: beamformer Dev driftscan (halfband)'"

    echo "python make_fbfobs_sb.py -o ruby --target 'J0437-4715' --backend dspsr"

done




# -fin-
