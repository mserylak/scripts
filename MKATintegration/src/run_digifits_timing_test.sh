#! /bin/bash

export LC_NUMERIC=C

if [ $# -eq 0 ]
then
    echo "Usage: $0 <target> [pol]"
    echo "Please specify a target such as: 'J0437-4715, J0835-4510'"
    exit 1
fi
target=$1

pol=1
if [ $# -eq 2 ]
then
    pol=$2
fi

backend='digifits'
for t in 0.0001531 0.000064 0.00003828
do
    echo
    if [ $pol == '1' ]
    then
        description="Power detected search mode single pol"
    fi
    if [ $pol == '2' ]
    then
        description="Autocorrelation search mode dual pol"
    fi
    if [ $pol == '4' ]
    then
        description="Semi-stokes search mode four pol"
    fi

    # half-band
    echo "python make_fbfobs_sb.py -o ruby --target '$target' --duration 60 --bw 428 --backend $backend --backend-args='-t $t -p $pol' --description='HBW: $description, t=$t'"
#     python make_fbfobs_sb.py -o ruby --target $target --duration 60 --bw 428 --backend $backend --backend-args="'-t $t -p $pol'" --description="'HBW: $description'"
    python make_fbfobs_sb.py -o ruby --target "$target" --duration 60 --bw 428 --backend $backend --backend-args="-t $t -p $pol" --description="HBW: $description, t=$t"
    python make_fbfobs_sb.py -o ruby --target "$target" --duration 120 --bw 428 --backend $backend --backend-args="-t $t -p $pol" --description="HBW: $description, t=$t"
    python make_fbfobs_sb.py -o ruby --target "$target" --duration 180 --bw 428 --backend $backend --backend-args="-t $t -p $pol" --description="HBW: $description, t=$t"

    # full-band
    echo "python make_fbfobs_sb.py -o ruby --target '$target' --duration 60 --bw 856 --backend $backend --backend-args='-t $t -p $pol' --description='FBW: $description, t=$t'"
    python make_fbfobs_sb.py -o ruby --target "$target" --duration 60 --bw 856 --backend $backend --backend-args="-t $t -p $pol" --description="FBW: $description, t=$t"

done

# -fin-
