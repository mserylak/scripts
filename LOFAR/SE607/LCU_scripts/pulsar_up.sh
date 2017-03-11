#!/usr/bin/env bash

# Copyright (C) 2017 by Maciej Serylak
# Licensed under the Academic Free License version 3.0
# This program comes with ABSOLUTELY NO WARRANTY.
# You are free to modify and redistribute this code as long
# as you do not remove the above attribution and reasonably
# inform recipients that you have modified the original work.

#   882589.650  -4924872.3200    3943729.3480   GBT           38.4331290508204, -79.8398384679332,    823.637373044156
#  2390490.000  -5564764.0000    1994727.0000   ARECIBO       18.3441417459825, -66.7527926727223,   482.803856249899
# -4554231.500   2816759.1000   -3454036.3000   PARKES       -32.998406398651,  148.26351001321,     414.759749681689
#  3822626.040   -154105.6500    5086486.0400   JODRELL       53.2365394291097,  -2.30857649865576,  179.411758022383
#  4324165.810    165927.1100    4670132.8300   NANCAY        47.3736017082624,   2.19747845066223,  190.943431356922
#  4033949.500    486989.4000    4900430.8000   EFFELSBERG    50.5248193846274,   6.88359151584425,  417.881571201608
#  5085442.780   2668263.4830   -2768697.0340   HartRAO      -25.8897519845581,  27.6853926097525,  1415.71618138906
#  3828445.659    445223.6000    5064921.5677   WSRT          52.915291872595,    6.63333413718364,   71.210372001864
#  3826577.462    461022.6240    5064892.5260   LOFAR         52.9151189679833,   6.86983283620003,   49.3500294256955
#  4034101.901    487012.4010    4900230.2100   DE601         50.5226040834545,   6.88365594878742,  360.993089747615
#  4152568.416    828788.8020    4754361.9260   DE602         48.501226921106,   11.2870466604831,   499.214455015957
#  3940296.126    816722.5320    4932394.1520   DE603         50.9793945678047,  11.7101282870573,   376.425702796318
#  3796380.254    877613.8090    5032712.2720   DE604         52.4378592173164,  13.0164819399188,    75.8433507084847
#  4005681.407    450968.3040    4926457.9400   DE605         50.8973466544674,   6.42343582520156,  139.232115182094
#  4324017.054    165545.1600    4670271.0720   FR606         47.3755242919458,   2.19250033617532,  182.09066780936
#  3370272.092    712125.5960    5349990.9340   SE607         57.3987574589978,  11.9308890388522,    41.3579993117601
#  4008462.280   -100376.9480    4943716.6000   UK608         51.1435426553869,  -1.43445875537285,  177.052691196091
#  2136819.194    810039.5757    5935299.0536   FI609         69.0710443645768,  20.7610478990429,   525.324950813316
#  3738429.284   1148245.7443    5021744.4160   PL610         52.2759328,        17.07416,           122.29
#  3850964.550   1439020.9853    4860515.2033   PL611         49.9649386,        20.4896131,         305.42
#  3551455.035   1334179.1738    5110190.7549   PL612         53.5939042,        20.5897506,         178.38
#  3307865.236   2487350.5410    4836939.7840   UTR2          49.6382040054817,  36.9413500027937,   149.999855332077
#  1656342.300   5797947.7700    2073243.1600   GMRT          19.0930027830705,  74.0565611576975,   497.000828543678
#  5109943.1050  2003650.7359   -3239908.3195   KAT7         -30.7213885708783,  21.4105542858234,  1037.99994549342
#  5109318.8410  2006836.3673   -3238921.7749   MEERKAT      -30.7110555556117   21.4438888892753   1034.99998227134
#  4323467.9155   166037.9873    4670758.5351   EMBRACE       47.382              2.1993             182.00000000000
# -4752329.700   2790505.9340   -3200483.747    NARRABRI     -30.3128702786745  149.5791005963390    239.585321234539
#   228310.702   4631922.9050    4367064.059    NANSHAN       43.4715093024277   87.1781350022324   2033.33327451069
# -1601192.000  -5041981.4000    3554871.400    VLA           34.0787512855409 -107.6183895352070   2117.09053677134
#  1656342.300   5797947.7700    2073243.160    GMRT          19.0930027830705   74.0565611576975    497.000828543678
# -1602196.600  -5042313.4700    3553971.510    LWA1          34.0688999746259 -107.6276700211350   2126.99664182309

site="SE607"
elevation=30

help()
{
  echo "pulsar_up.sh: combines outputs of sid.pl, azza.pl and azlst.pl"
  echo "Usage: pulsar_up.sh <pulsar_name> <observatory> <elevation> <time>"
  echo "where:"
  echo "      pulsar_name - B or J name of a pulsar (required argument)"
  echo "      observatory - Observatory name (optional argument, default: $site)"
  echo "                    Use pre-defined observatory. Following are available:"
  echo "                    GBT, Arecibo, Parkes, Jodrell, Nancay, Effelsberg, HartRAO,"
  echo "                    WSRT, LOFAR, DE601, DE602, DE603, DE604, DE605, FR606,"
  echo "                    SE607, UK608, FI609, PL610, PL611, PL612, UTR2, GMRT,"
  echo "                    KAT7, MeerKAT, EMBRACE."
  echo "      elevation   - Elevation in degrees (optional argument, default: $elevation)"
  echo "      time        - UTC time in format YYYY-MM-DDThh:mm:ss.sss (optional argument, default: now)"
  echo ''
  echo "e.g. pulsar_up.sh B0329+54 $site $elevation"
  exit
}

if [ -z "$1" ] || [ $1 = "-h" ] ; then
  help
else
  source=$1 # get source name
  source=`echo $source | awk '{print toupper($0)}'` # change argument letters to upper-case
  #echo $source
  source_info=(`psrcat -o short -nohead -nonumber -c "name raj decj" $source`) # use psrcat to query for pulsar parameters
  #echo ${source_info[@]}
  if [ ${source_info[0]} = "WARNING:" ] || [ ${source_info[0]} = "Unknown" ] ; then # check if source is known for psrcat
    echo ''
    echo "$source not in catalogue."
    echo ''
    exit
  fi
  raj=`echo ${source_info[1]}` # get the RA (J2000) of the pulsar from $source_info array
  #echo $raj
  decj=`echo ${source_info[2]}` # get the Dec (J2000) of the pulsar from $source_info array
  #echo $decj
  if [ -n "$2" ] ; then
     site=$2
  fi
  #site=${site,,} # convert to lower case
  site=`echo ${site} | awk '{print tolower($0)}'`
  #echo $site
  if [ -n "$3" ] ; then
     elevation=$3
  fi
  if [ -n "$4" ] ; then
    time=$4
    sid.pl -site $site -t $4
    azza.pl -ra $raj -dec $decj -site $site -t $4
    azlst.pl -ra $raj -dec $decj -el $elevation -site $site
  else
    sid.pl -site $site
    azza.pl -ra $raj -dec $decj -site $site
    azlst.pl -ra $raj -dec $decj -el $elevation -site $site
  fi
fi
