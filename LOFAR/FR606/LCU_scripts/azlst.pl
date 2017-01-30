#!/usr/bin/perl
#
# script calculates the azimuth and hour angle (and LST)
# (actually the min and max values of HA and LST)
# of the source with pointed RA and DEC for pointed
# elevation (zenith angle)
#
# Vlad Kondratiev (c)
# modified by Maciej Serylak
#
use Math::Trig;
use Getopt::Long;

$pi = 3.14159265359;
$rad = $pi/180.;

# Latitude
$phiGBT=38.4331290508204; # GBT
$phiARECIBO=18.3441417459825; # ARECIBO
$phiPARKES=-32.9984063986510; # PARKES
$phiJODRELL=53.2365394291097; # JODRELL
$phiNANCAY=47.3736017082624; # NANCAY
$phiEFFELSBERG=50.5248193846274; # EFFELSBERG
$phiHARTRAO=-25.8897519845581; # HartRAO
$phiWSRT=52.9152918725950; # WSRT
$phiLOFAR=52.9151189679833; # LOFAR
$phiDE601=50.5226040834545; # DE601
$phiDE602=48.5012269211060; # DE602
$phiDE603=50.9793945678047; # DE603
$phiDE604=52.4378592173164; # DE604
$phiDE605=50.8973466544674; # DE605
$phiFR606=47.3755242919458; # FR606
$phiSE607=57.3987574589978; # SE607
$phiUK608=51.1435426553869; # UK608
$phiFI609=69.0710443645768; # FI609
$phiUTR2=49.6382040054817; # UTR2
$phiGMRT=19.0930027830705; # GMRT
$phiKAT7=-30.7213885708783; # KAT7
$phiEMBRACE=47.382; # EMBRACE

# Longitude
$lambdaGBT=-79.8398384679332; # GBT
$lambdaARECIBO=-66.7527926727223; # ARECIBO
$lambdaPARKES=148.263510013210; # PARKES
$lambdaJODRELL=-2.30857649865576; # JODRELL
$lambdaNANCAY=2.19747845066223; # NANCAY
$lambdaEFFELSBERG=6.88359151584425; # EFFELSBERG
$lambdaHARTRAO=27.6853926097525; # HartRAO
$lambdaWSRT=6.63333413718364; # WSRT
$lambdaLOFAR=6.86983283620003; # LOFAR
$lambdaDE601=6.88365594878742; # DE601
$lambdaDE602=11.2870466604831; # DE602
$lambdaDE603=11.7101282870573; # DE603
$lambdaDE604=13.0164819399188; # DE604
$lambdaDE605=6.42343582520156; # DE605
$lambdaFR606=2.19250033617532; # FR606
$lambdaSE607=11.9308890388522; # SE607
$lambdaUK608=-1.43445875537285; # UK608
$lambdaFI609=20.7610478990429; # FI609
$lambdaUTR2=36.9413500027937; # UTR2
$lambdaGMRT=74.0565611576975; # GMRT
$lambdaKAT7=21.4105542858234; # KAT7
$lambdaEMBRACE=2.1993; # EMBRACE

$is_never_set = 0;    # flag, if 1 then source never sets
$is_never_rise = 0;   # flag, if 1 then source never rises
$is_never_above = 0;  # flag, if 1 then source is never above this EL (no matter circumpolar or not)
$ra = "";
$dec = "";
$EL = 30.;

# if there are no parameters in command line
# help is called and program normally exit
&help($0) && exit if $#ARGV < 0;

# Parse command line
GetOptions ( "el=f" => \$EL,   # - elevation (in deg)
             "ra=s" => \$ra,   # - RA of the source "hh:mm:ss.sss"
             "dec=s" => \$dec, # - DEC of the source "[+|-]dd:mm:ss.ssss"
             "lat=f" => \$phi, # - latitude (degrees)
             "lon=f" => \$lambda, # - longitude (degrees)
             "site=s" => \$site, # - site
             "h" => \$help);   # - to print the help

if ($help) { &help($0); exit 0; }

if ($ra eq "" || $dec eq "") {
 &error ("No RA or DEC commanded!");
}

$site = lc($site);
if ($site eq "gbt") {
 $lambda=$lambdaGBT;
 $phi=$phiGBT;
} elsif ($site eq "arecibo") {
 $lambda=$lambdaARECIBO;
 $phi=$phiARECIBO;
} elsif ($site eq "parkes") {
 $lambda=$lambdaPARKES;
 $phi=$phiPARKES;
} elsif ($site eq "jodrell") {
 $lambda=$lambdaJODRELL;
 $phi=$phiJODRELL;
} elsif ($site eq "nancay") {
 $lambda=$lambdaNANCAY;
 $phi=$phiNANCAY;
} elsif ($site eq "effelsberg") {
 $lambda=$lambdaEFFELSBERG;
 $phi=$phiEFFELSBERG;
} elsif ($site eq "hartrao") {
 $lambda=$lambdaHARTRAO;
 $phi=$phiHARTRAO;
} elsif ($site eq "wsrt") {
 $lambda=$lambdaWSRT;
 $phi=$phiWSRT;
} elsif ($site eq "lofar") {
 $lambda=$lambdaLOFAR;
 $phi=$phiLOFAR;
} elsif ($site eq "de601") {
 $lambda=$lambdaDE601;
 $phi=$phiDE601;
} elsif ($site eq "de602") {
 $lambda=$lambdaDE602;
 $phi=$phiDE602;
} elsif ($site eq "de603") {
 $lambda=$lambdaDE603;
 $phi=$phiDE603;
} elsif ($site eq "de604") {
 $lambda=$lambdaDE604;
 $phi=$phiDE604;
} elsif ($site eq "de605") {
 $lambda=$lambdaDE605;
 $phi=$phiDE605;
} elsif ($site eq "fr606") {
 $lambda=$lambdaFR606;
 $phi=$phiFR606;
} elsif ($site eq "se607") {
 $lambda=$lambdaSE607;
 $phi=$phiSE607;
} elsif ($site eq "uk608") {
 $lambda=$lambdaUK608;
 $phi=$phiUK608;
} elsif ($site eq "fi609") {
 $lambda=$lambdaFI609;
 $phi=$phiFI609;
} elsif ($site eq "utr2") {
 $lambda=$lambdaUTR2;
 $phi=$phiUTR2;
} elsif ($site eq "gmrt") {
 $lambda=$lambdaGMRT;
 $phi=$phiGMRT;
} elsif ($site eq "kat7") {
 $lambda=$lambdaKAT7;
 $phi=$phiKAT7;
} elsif ($site eq "embrace") {
 $lambda=$lambdaEMBRACE;
 $phi=$phiEMBRACE;
} elsif ($site eq "" and $lambda eq "" and $phi eq "") {
 $lambda=$lambdaFR606;
 $phi=$phiFR606;
} else {
 &error ("Unknown site!"); 
}

if ($EL eq "") {
 &error ("Elevation is not defined!");
}

$dec1 = &dec2rad ($dec);

# zenith angle
$ZA = 90. - $EL;
$ZA = sprintf ("%.1f", $ZA);
$EL = sprintf ("%.1f", $EL);

print "\n";
print "Source: RA = $ra  DEC = $dec\n";
print "Site: LAT = $phi deg  LON = $lambda deg\n";
print "\n";
print "EL = $EL deg (ZA = $ZA deg)\n";

# checking if the source is circumpolar or not (never set or rise) at this latitude and elevation
# I'm using 0.001 as a tolerance to compare correctly two float values
if (($phi >= 0. && $dec1/$rad >= 90. - $phi + $EL - 0.001) || ($phi < 0. && $dec1/$rad <= -(90. + $phi + $EL - 0.001))) {  # never sets
  $is_never_set = 1;
  # calculating the minimum EL of the source
  if ($phi >= 0.) { $mEL = sprintf ("%.1f", $dec1/$rad + $phi - 90.); }
   else { $mEL = sprintf ("%.1f", -1. * ($dec1/$rad + $phi) - 90.); }
}
if (($phi >= 0. && $dec1/$rad < -(90. - $phi) + $EL + 0.001) || ($phi < 0. && $dec1/$rad > 90. + $phi - $EL - 0.001)) { # never rise
  $is_never_rise = 1;
  # calculating the maximum EL of the source
  if ($phi >= 0.) { $mEL = sprintf ("%.1f", $dec1/$rad - $phi + 90.); }
   else { $mEL = sprintf ("%.1f", $phi - $dec1/$rad + 90.); }
}

# getting the EL at transit to compare with given EL 
$EL_transit = sprintf ("%.1f", 90. - &get_ZA ($dec1, $phi, 0.0));
if ($EL >= $EL_transit - 0.001) {
 $is_never_above = 1;
}

# Calculating the HA, AZ range and LST set and rise for sources
# that are not circumpolar
if ($is_never_set == 0 && $is_never_rise == 0 && $is_never_above == 0) {
 # hour angle (absolute value) in rad
 # actually there are 2 values +- $HA
 $HA = &get_HA ($ZA, $dec1, $phi);
 $HAmin = -$HA;
 $HAmax = $HA;
 # in degrees (from South clockwise)
 $AZmin = &get_AZ ($dec1, $phi, $HAmin);
 $AZmax = &get_AZ ($dec1, $phi, $HAmax);

 $alphah = &time2hour($ra);
 $sidmin = `echo \"scale=20\n$alphah - ($HA / $rad / 15.)\" | bc -l`;
 $sidmax = `echo \"scale=20\n$alphah + ($HA / $rad / 15.)\" | bc -l`;
 if ($sidmin < 0.) { $sidmin += 24.; }
 if ($sidmax >= 24.) { $sidmax -= 24.; }
 $LSTmin = &hour2time ($sidmin);
 $LSTmax = &hour2time ($sidmax);

 $is_always = ($phi >= 0. ? "   [always North]" : "   [always South]");
 printf ("AZ = [ %.1f ; %.1f ] deg%s\n", $AZmin, $AZmax, abs($dec1/$rad)>=abs($phi) ? $is_always : "");
 $hapres = $HA / $rad / 15.; 
 $hapres_label = "h";
 if (abs($hapres) < 1) { 
  $hapres *= 60.; 
  $hapres_label = "min"; 
  if (abs($hapres) < 1) {
   $hapres *= 60.; 
   $hapres_label = "sec"; 
  }
 }
 printf ("EL at transit = %.1f deg\n", $EL_transit);
 printf ("HA =  +/- %.2f %s  [Duration = %.2f %s]\n", $hapres, $hapres_label, 2 * $hapres, $hapres_label);
 printf ("LST = [rise: %s] [set: %s]\n", $LSTmin, $LSTmax);
 print "\n";
}

# if source never sets
if ($is_never_set == 1) {
 if (abs($dec1/$rad)>=abs($phi)) {
  printf ("AZ - always %s\n", $phi >= 0. ? "North" : "South");
 }
 print "Circumpolar source (never sets) at this LAT and EL\n";
 print "The minimum EL = $mEL deg\n";
}
# if source never rises
if ($is_never_rise == 1) {
 print "Circumpolar source (never rises) at this LAT and EL\n";
 print "The maximum EL = $mEL deg\n";
}
# if source is never above given EL
if ($is_never_above == 1 && $is_never_rise == 0) {
 print "The source is never above the given EL\n";
 print "Tha maximum EL = $EL_transit deg\n";
}

# help
sub help {
 local ($prg) = @_;
 $prg = `basename $prg`;
 chomp $prg;
 print "$prg - calculates AZ and LST of rise and set for a given source at given observatory\n";
 print "Usage: $prg [options]\n";
 print "        -el  EL     - elevation in degrees, default = 30 deg\n";
 print "        -ra  RA     - right assention of the source where RA is in \"hh:mm:ss.sss\"\n";
 print "        -dec DEC    - declination of the source where DEC is in \"[+\-]dd:mm:ss.sss\"\n";
 print "        -lat PHI    - latitude in degrees (default - FR606)\n";
 print "        -lon LAMBDA - longitude in degrees (default - FR606)\n";
 print "                      Western longitudes are negative!\n";
 print "        -site NAME  - Use pre-defined observatory. Following are available: \n";
 print "                      GBT, Arecibo, Parkes, Jodrell, Nancay, Effelsberg, HartRAO,\n";
 print "                      WSRT, LOFAR, DE601, DE602, DE603, DE604, DE605, FR606,\n";
 print "                      SE607, UK608, FI609, UTR2, GMRT, KAT7, EMBRACE.\n";
 print "        -h          - print this help\n";
}

# unique subroutine to output errors
# one input parameter (string): the error message
sub error {
 my ($error) = @_;
 print "Error: $error\n";
 exit 1;
}

# transform dec format into radians
sub dec2rad {
 my ($d) = @_;
 $deg = $d; $deg =~ s/^([+-]?\d\d)\:.*$/$1/;
 $deg *= 1;
 $mm = $d; $mm =~ s/^[+-]?\d\d\:(\d\d)\:.*$/$1/;
 $ss = $d; $ss =~ s/^[+-]?\d\d\:\d\d\:(\d\d.*)$/$1/;
 if ($deg < 0) {
  $newd = `echo \"($deg - $mm / 60. - $ss / 3600.) * $rad\" | bc -l`;
 } else {
  $newd = `echo \"($deg + $mm / 60. + $ss / 3600.) * $rad\" | bc -l`;
 }
 chomp $newd;
 return $newd;
}

# get hour angle (absolute value) in radians
# actually there are 2 values +- 
sub get_HA {
 my ($zen, $delta, $shirota) = @_;

 $ha = acos ( (cos ($zen * $rad) - sin ($delta) * sin ($shirota * $rad)) / (cos ($delta) * cos ($shirota * $rad)) );
 return $ha;
}

# get zenith angle (in degrees)
sub get_ZA {
 my ($delta, $shirota, $hour_angle) = @_;

 $zen = acos ( sin ($delta) * sin ($shirota * $rad) + cos ($delta) * cos ($shirota * $rad) * cos ($hour_angle) );
 $zen /= $rad;
 return $zen;
}

# get azimuth (in degrees, from North clockwise)
sub get_AZ {
 my ($delta, $shirota, $hour_angle) = @_;

 $azim = atan2 ( cos ($delta) * sin ($hour_angle), -sin ($delta) * cos ($shirota * $rad) + cos ($delta) * sin ($shirota * $rad) * cos ($hour_angle) );
 $azim /= $rad;
 $azim += 180.;
 while ($azim >= 360.) { $azim -= 360.; }
 return $azim; 
}

# transform time format into hours
sub time2hour {
 my ($time) = @_;
 $hh = $time; $hh =~ s/^(\d\d)\:.*$/$1/;
 $mm = $time; $mm =~ s/^\d\d\:(\d\d)\:.*$/$1/;
 $ss = $time; $ss =~ s/^\d\d\:\d\d\:(\d\d.*)$/$1/;
 $t = `echo \"scale=20\n($hh + $mm / 60. + $ss / 3600.)\" | bc -l`;
 chomp $t;
 return $t;
}

# transform hours into time format
sub hour2time {
 my ($hours) = @_;
 $hh = int ($hours);
 $mm = int ( 60. * ($hours - $hh) );
 $ss = (($hours - $hh) * 60. - $mm) * 60.;
 $time = sprintf ("%02d:%02d:%02d", $hh, $mm, $ss);
 return $time;
}
