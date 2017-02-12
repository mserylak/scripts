#!/usr/bin/env bash

help()
{
   echo ''
   echo "lcu_observe.sh - script executing beamctl commands for LOFAR single station LCU."
   echo ''
   echo "Usage: lcu_observe.sh <lba/hba/lba8/hba8> <start_subband> <psr> <pulsar name>"
   echo "   or: lcu_observe.sh <lba/hba/lba8/hba8> <start_subband> <radec> <ra> <dec>"
   echo ''
   echo "where:"
   echo "      lba/hba/lba8/hba8  - LOFAR antennas configuration (hba8 - RCUs must be set to send 8-bit data)."
   echo "      start_subband      - start subband for allocating 244 consecutive subbands (not parsed in hba8 mode)."
   echo "      psr                - pointing using pulsar source name followed by B or J pulsar name known by psrcat."
   echo "      radec              - pointing using J2000 RA and Dec coordinates."
   echo ''
   echo "e.g. lcu_observe.sh hba 220 psr B0329+54"
   echo "e.g. lcu_observe.sh hba8 psr B0329+54"
   echo "e.g. lcu_observe.sh lba 157 radec 21:45:50.46412 -07:50:18.4399"
   echo "e.g. lcu_observe.sh lba8 radec 21:45:50.46412 -07:50:18.4399"
   echo ''
   exit
}

prepare_commands()
{
   pos_rad=(`echo ${rajd} ${decjd} | awk -v pi=3.1415926535 '{printf "%.6f %.6f\n",$1/180.0*pi, $2/180.0*pi}'`) # calculate position of the source in radians
   #echo ${pos_rad[@]}
   if [ ${antennas} = "LBA" ] ; then # prepare beamctl commands for LBA observations
      /usr/bin/killall -9 beamctl
      /opt/lofar/bin/rspctl --rcumode=3
      /opt/lofar/bin/rspctl --rcuenable=1
      /opt/lofar/bin/rspctl --specinv=0
      /usr/bin/sleep 20
      /opt/lofar/bin/beamctl --antennaset=LBA_INNER --rcus=0:191 --band=30_90 --beamlets=0:243 --subbands=${startsubband}:$((startsubband+243)) --digdir=${pos_rad[0]},${pos_rad[1]},J2000 &
      #/opt/lofar/bin/beamctl --antennaset=LBA_INNER --rcus=0:191 --band=30_90 --beamlets=0:60 --subbands=${startsubband}:$((startsubband+60)) --digdir=${pos_rad[0]},${pos_rad[1]},J2000 &
      #/opt/lofar/bin/beamctl --antennaset=LBA_INNER --rcus=0:191 --band=30_90 --beamlets=61:121 --subbands=$((startsubband+61)):$((startsubband+121)) --digdir=${pos_rad[0]},${pos_rad[1]},J2000 &
      #/opt/lofar/bin/beamctl --antennaset=LBA_INNER --rcus=0:191 --band=30_90 --beamlets=122:182 --subbands=$((startsubband+122)):$((startsubband+182)) --digdir=${pos_rad[0]},${pos_rad[1]},J2000 &
      #/opt/lofar/bin/beamctl --antennaset=LBA_INNER --rcus=0:191 --band=30_90 --beamlets=183:243 --subbands=$((startsubband+183)):$((startsubband+243)) --digdir=${pos_rad[0]},${pos_rad[1]},J2000 &
   elif [ ${antennas} = "HBA" ] ; then # prepare beamctl commands for HBA observations
      /usr/bin/killall -9 beamctl
      /opt/lofar/bin/rspctl --rcuenable=0
      /opt/lofar/bin/rspctl --rcumode=0
      /opt/lofar/sbin/poweruphba.sh 5
      #/data/home/user1/poweruphba_broken2.sh
      /usr/bin/sleep 20
      /opt/lofar/bin/beamctl --antennaset=HBA_DUAL --rcus=0:191 --band=110_190 --beamlets=0:243 --subbands=${startsubband}:$((startsubband+243)) --anadir=${pos_rad[0]},${pos_rad[1]},J2000 --digdir=${pos_rad[0]},${pos_rad[1]},J2000 &
      #/opt/lofar/bin/beamctl --antennaset=HBA_DUAL --rcus=0:191 --band=110_190 --beamlets=0:60 --subbands=${startsubband}:$((startsubband+60)) --anadir=${pos_rad[0]},${pos_rad[1]},J2000 --digdir=${pos_rad[0]},${pos_rad[1]},J2000 &
      #/opt/lofar/bin/beamctl --antennaset=HBA_DUAL --rcus=0:191 --band=110_190 --beamlets=61:121 --subbands=$((startsubband+61)):$((startsubband+121)) --anadir=${pos_rad[0]},${pos_rad[1]},J2000 --digdir=${pos_rad[0]},${pos_rad[1]},J2000 &
      #/opt/lofar/bin/beamctl --antennaset=HBA_DUAL --rcus=0:191 --band=110_190 --beamlets=122:182 --subbands=$((startsubband+122)):$((startsubband+182)) --anadir=${pos_rad[0]},${pos_rad[1]},J2000 --digdir=${pos_rad[0]},${pos_rad[1]},J2000 &
      #/opt/lofar/bin/beamctl --antennaset=HBA_DUAL --rcus=0:191 --band=110_190 --beamlets=183:243 --subbands=$((startsubband+183)):$((startsubband+243)) --anadir=${pos_rad[0]},${pos_rad[1]},J2000 --digdir=${pos_rad[0]},${pos_rad[1]},J2000 &
   elif [ ${antennas} = "LBA8" ] ; then # prepare beamctl commands for LBA observations
      /usr/bin/killall -9 beamctl
      /opt/lofar/bin/rspctl --rcumode=3
      /opt/lofar/bin/rspctl --rcuenable=1
      /opt/lofar/bin/rspctl --specinv=0
      /usr/bin/sleep 20
      /opt/lofar/bin/beamctl --antennaset=LBA_INNER --rcus=0:191 --band=30_90 --beamlets=0:487 --subbands=12:499 --digdir=${pos_rad[0]},${pos_rad[1]},J2000 &
      #/opt/lofar/bin/beamctl --antennaset=LBA_INNER --rcus=0:191 --band=30_90 --beamlets=0:121 --subbands=12:133 --digdir=${pos_rad[0]},${pos_rad[1]},J2000 &
      #/opt/lofar/bin/beamctl --antennaset=LBA_INNER --rcus=0:191 --band=30_90 --beamlets=122:243 --subbands=134:255 --digdir=${pos_rad[0]},${pos_rad[1]},J2000 &
      #/opt/lofar/bin/beamctl --antennaset=LBA_INNER --rcus=0:191 --band=30_90 --beamlets=244:365 --subbands=256:377 --digdir=${pos_rad[0]},${pos_rad[1]},J2000 &
      #/opt/lofar/bin/beamctl --antennaset=LBA_INNER --rcus=0:191 --band=30_90 --beamlets=366:487 --subbands=378:499 --digdir=${pos_rad[0]},${pos_rad[1]},J2000 &
   elif [ ${antennas} = "HBA8" ] ; then # prepare beamctl commands for 8 bit mode HBA observations
      /usr/bin/killall -9 beamctl
      /opt/lofar/bin/rspctl --rcuenable=0
      /opt/lofar/bin/rspctl --rcumode=0
      /opt/lofar/sbin/poweruphba.sh 5
      #/data/home/user1/poweruphba_broken2.sh
      /usr/bin/sleep 20
      /opt/lofar/bin/beamctl --antennaset=HBA_DUAL --rcus=0:191 --band=110_190 --beamlets=0:487 --subbands=12:499 --anadir=${pos_rad[0]},${pos_rad[1]},J2000 --digdir=${pos_rad[0]},${pos_rad[1]},J2000 &
      #/opt/lofar/bin/beamctl --antennaset=HBA_DUAL --rcus=0:191 --band=110_190 --beamlets=0:121 --subbands=12:133 --anadir=${pos_rad[0]},${pos_rad[1]},J2000 --digdir=${pos_rad[0]},${pos_rad[1]},J2000 &
      #/opt/lofar/bin/beamctl --antennaset=HBA_DUAL --rcus=0:191 --band=110_190 --beamlets=122:243 --subbands=134:255 --anadir=${pos_rad[0]},${pos_rad[1]},J2000 --digdir=${pos_rad[0]},${pos_rad[1]},J2000 &
      #/opt/lofar/bin/beamctl --antennaset=HBA_DUAL --rcus=0:191 --band=110_190 --beamlets=244:365 --subbands=256:377 --anadir=${pos_rad[0]},${pos_rad[1]},J2000 --digdir=${pos_rad[0]},${pos_rad[1]},J2000 &
      #/opt/lofar/bin/beamctl --antennaset=HBA_DUAL --rcus=0:191 --band=110_190 --beamlets=366:487 --subbands=378:499 --anadir=${pos_rad[0]},${pos_rad[1]},J2000 --digdir=${pos_rad[0]},${pos_rad[1]},J2000 &
   fi
}

if [ -z "${3}" ] || [ ${1} = "-h" ] ; then
   help
else
   soft_level=`swlevel | sed -n 1p | tr -d [:alpha:] | sed 's/ //g'`
   if [ ${soft_level} != "3" ] ; then
      echo ''
      echo "WARNING! LCU software in (incorrect) level ${soft_level}"
      echo ''
      exit
   fi
   antennas=${1} # get the type of antennas
   antennas=`echo ${antennas} | awk '{print toupper($0)}'` # change argument letters to upper-case
   #echo ${antennas}
   if [ ${antennas} = "HBA8" -o ${antennas} = "LBA8" ] ; then
#      bit_mode=`rspctl --bitmode | grep -e "RSP\[00\] | awk '{print $4}'"`
#      #echo $bit_mode
#      if [ $bit_mode != "8" ] ; then
#         echo ''
#         echo "WARNING! RCUs in (incorrect) bit mode $bit_mode"
#         echo ''
#         exit
#      fi
      mode=${2}
      mode=`echo ${mode} | awk '{print toupper($0)}'` # change argument letters to upper-case
      if [ ${mode} = "PSR" ] ; then # check if PSR...
         source=${3} # get source name
         source=`echo ${source} | awk '{print toupper($0)}'` # change argument letters to upper-case
         #echo ${source}
         source_info=(`psrcat -x -o short -c "name rajd decjd" ${source}`) # use psrcat to query for pulsar parameters
         #echo ${source_info[@]}
         if [ ${source_info[0]} = "WARNING:" ] ; then # check if source is known for psrcat
            echo ''
            echo "${source} not in catalogue. Maybe use RADec mode instead?"
            echo ''
            exit
         fi
         rajd=`echo ${source_info[1]}` # get the RA (in degrees, J2000) of the pulsar from $source_info array
         #echo ${rajd}
         decjd=`echo ${source_info[2]}` # get the Dec (in degrees, J2000) of the pulsar from $source_info array
         #echo ${decjd}
         prepare_commands
      elif [ ${mode} = "RADEC" ] ; then # ...or RAJDecJ mode are called
         raj=$3 # get the RA (in HH:MM:SS, J2000) of the pointing position
         #echo ${raj}
         rajd=`echo ${raj} | sed s/\\:/" "/g | awk '{printf "%.6f\n",$1*15+$2/4+$3/240}'` # calculate position of the source in radians
         #echo ${rajd}
         decj=$4 # get the Dec (in DD:MM:SS, J2000) of the pointing position
         #echo ${decj}
         decj1=`echo ${decj} | awk -F\: '{gsub("+",""); print $1}'` # get the degree value
         #echo $decj1
         if [ $(echo "$decj1 < 0"| bc -l) -eq 1 ] ; then # check if it is negative
            decjd=`echo ${decj} | sed s/\\:/" "/g | awk '{printf "-%.6f\n",($1*-1)+$2/60+$3/3600}'`
            #echo ${decjd}
         else
            decjd=`echo ${decj} | sed s/\\:/" "/g | awk '{printf "%.6f\n",$1+$2/60+$3/3600}'`
            #echo ${decjd}
         fi
         prepare_commands
      else
         echo ''
         echo "Invalid observing mode! Exiting..."
         echo ''
         exit
      fi
   elif [ ${antennas} = "LBA" -o ${antennas} = "HBA" ] ; then # check if the name of antennas configuration is set to LBA, HBA or...
      startsubband=${2}
      #echo ${startsubband}
      if [ ${startsubband} -eq ${startsubband} 2> /dev/null ]; then # check if ${startsubband} is a number
         if [ $(echo "${startsubband} > 268"| bc -l) -eq 1 ] ; then # start subband must be less than 268 or the range will not fit in 511 subbands available for LOFAR station
            echo ''
            echo "Invalid subband value! Allowed start subband range from 0 to 268. Exiting..."
            echo ''
            exit
         fi
      else
         echo ''
         echo "Invalid subband value! Allowed start subband range from 0 to 268. Exiting..."
         echo ''
         exit
      fi
      mode=${3}
      mode=`echo ${mode} | awk '{print toupper($0)}'` # change argument letters to upper-case
      if [ ${mode} = "PSR" ] ; then # check if PSR...
         source=${4} # get source name
         source=`echo ${source} | awk '{print toupper($0)}'` # change argument letters to upper-case
         #echo ${source}
         source_info=(`psrcat -x -o short -c "name rajd decjd" ${source}`) # use psrcat to query for pulsar parameters
         #echo ${source_info[@]}
         if [ ${source_info[0]} = "WARNING:" ] ; then # check if source is known for psrcat
            echo ''
            echo "${source} not in catalogue. Maybe use RADec mode instead?"
            echo ''
            exit
         fi
         rajd=`echo ${source_info[1]}` # get the RA (J2000) of the pulsar from ${source_info} array
         #echo ${rajd}
         decjd=`echo ${source_info[2]}` # get the Dec (J2000) of the pulsar from ${source_info} array
         #echo ${decjd}
         prepare_commands
      elif [ ${mode} = "RADEC" ] ; then # ...or RAJDecJ mode are called
         raj=${4} # get the RA (in HH:MM:SS, J2000) of the pointing position
         #echo ${raj}
         rajd=`echo ${raj} | sed s/\\:/" "/g | awk '{printf "%.6f\n",$1*15+$2/4+$3/240}'` # calculate position of the source in radians
         #echo ${rajd}
         decj=${5} # get the Dec (in DD:MM:SS, J2000) of the pointing position
         #echo ${decj}
         decj1=`echo ${decj} | awk -F\: '{gsub("+",""); print $1}'` # get the degree value
         #echo $decj1
         if [ $(echo "$decj1 < 0"| bc -l) -eq 1 ] ; then # check if it is negative
            decjd=`echo ${decj} | sed s/\\:/" "/g | awk '{printf "-%.6f\n",($1*-1)+$2/60+$3/3600}'`
         else
            decjd=`echo ${decj} | sed s/\\:/" "/g | awk '{printf "%.6f\n",$1+$2/60+$3/3600}'`
         fi
         prepare_commands
      else
         echo ''
         echo "Invalid observing mode! Exiting..."
         echo ''
         exit
      fi
   else
      echo ''
      echo "Invalid antennas configuration! Exiting..."
      echo ''
      exit
   fi
fi
