#!/usr/bin/env perl
#
# script calculates the azimuth and zenith angle (elevation)
# of the source with pointed RA and DEC for pointed time
# the script also has functions to calculate siderial time
# (based on my sid.pl) for specific time or at "now" time
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
$phiPL610=52.2759328000000; # PL610
$phiPL611=49.9649386000000; # PL611
$phiPL612=53.5939042000000; # PL612
$phiUTR2=49.6382040054817; # UTR2
$phiGMRT=19.0930027830705; # GMRT
$phiKAT7=-30.7213885708783; # KAT7
$phiMEERKAT=-30.7110555556117; # MeerKAT
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
$lambdaPL610=17.0741606000000; # PL610
$lambdaPL611=20.4896131000000; # PL611
$lambdaPL612=20.5897506000000; # PL612
$lambdaUTR2=36.9413500027937; # UTR2
$lambdaGMRT=74.0565611576975; # GMRT
$lambdaKAT7=21.4105542858234; # KAT7
$lambdaMEERKAT=21.4438888892753 ; # MeerKAT
$lambdaEMBRACE=2.1993; # EMBRACE

$ra = "";
$dec = "";
$UTC = "";
$site = "";
$lambda = "";
$phi = "";

# if there are no parameters in command line
# help is called and program normally exit
&help($0) && exit if $#ARGV < 0;

# Parse command line
GetOptions ( "t=s" => \$UTC,   # - time
             "ra=s" => \$ra,   # - RA of the source "hh:mm:ss.sss"
             "dec=s" => \$dec, # - DEC of the source "[+|-]dd:mm:ss.ssss"
             "lat=f" => \$phi, # - latitude (degrees)
             "lon=f" => \$lambda, # - longitude (degrees)
             "site=s" => \$site, # - site
             "h" => \$help);   # - to print the help

if ($help) { &help($0); exit 0; }

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
} elsif ($site eq "pl610") {
 $lambda=$lambdaPL610;
 $phi=$phiPL610;
} elsif ($site eq "pl611") {
 $lambda=$lambdaPL611;
 $phi=$phiPL611;
} elsif ($site eq "pl612") {
 $lambda=$lambdaPL612;
 $phi=$phiPL612;
} elsif ($site eq "utr2") {
 $lambda=$lambdaUTR2;
 $phi=$phiUTR2;
} elsif ($site eq "gmrt") {
 $lambda=$lambdaGMRT;
 $phi=$phiGMRT;
} elsif ($site eq "kat7") {
 $lambda=$lambdaKAT7;
 $phi=$phiKAT7;
} elsif ($site eq "meerkat") {
 $lambda=$lambdaMEERKAT;
 $phi=$phiMEERKAT;
} elsif ($site eq "embrace") {
 $lambda=$lambdaEMBRACE;
 $phi=$phiEMBRACE;
} elsif ($site eq "" and $lambda eq "" and $phi eq "") {
 $lambda=$lambdaFR606;
 $phi=$phiFR606;
 $site="fr606"
} else {
 &error ("Unknown site!"); 
}

if ($UTC eq "") {
 $UTC = &get_curtime();
}

# also checking if UTC is given in another format, namely YYYY-MM-DDTHH:MM:SS[.SSS]
# if it's in different format, then redo it to usual format
if ($UTC =~ /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.?\d*$/) {
 $UTC = &time_reformat($UTC);
}

if ($ra eq "" || $dec eq "") {
 &error ("No RA or DEC commanded!");
} 

if ($phi eq "") {
 &error ("Latitude is not defined!");
} 

if ($lambda eq "") {
 &error ("Longitude is not defined!");
} 

if ($site ne "") {
 $LST = `sid.pl -t \"$UTC\" -site $site | grep LST | awk '{print \$2}' -`;
} else {
 $LST = `sid.pl -t \"$UTC\" -lon $lambda | grep LST | awk '{print \$2}' -`;
}

chomp $LST;
$HA = &get_HA ($LST, $ra);
$dec1 = &dec2rad ($dec);

# in degrees
$ZA = &get_ZA ($dec1, $phi, $HA);
$ZA = sprintf ("%.1f", $ZA);
# in degrees
$EL = 90. - $ZA;
$EL = sprintf ("%.1f", $EL);
# in degrees (from South clockwise)
$AZ = &get_AZ ($dec1, $phi, $HA);
$AZ = sprintf ("%.1f", $AZ);

print "\n";
print "Source: RA = $ra  DEC = $dec\n";
print "Site: LAT = $phi deg  LON = $lambda deg\n";
print "\n";
printf ("UTC: %s\n", &time2str($UTC));
printf ("LST: %s\n", &time2str($LST));
$hapres = $HA / $rad / 15.; 
$hapres_label = "h";
#if (abs($hapres) < 1) { 
# $hapres *= 60.; 
# $hapres_label = "min"; 
# if (abs($hapres) < 1) {
#  $hapres *= 60.; 
#  $hapres_label = "sec"; 
# }
#}
printf ("HA = %.2f %s\n", $hapres, $hapres_label);
print "EL = $EL deg (ZA = $ZA deg)\n";
print "AZ = $AZ deg\n";
print "\n";

# help
sub help {
 local ($prg) = @_;
 $prg = `basename $prg`;
 chomp $prg;
 print "$prg: calculates AZ, EL(ZA), HA  for a given source and time at given observatory\n";
 print "Usage: $prg [options]\n";
 print "        -t   TIME   - UTC time in format \"DD.MM.YYYY hh:mm:ss.sss\" or \"YYYY-MM-DDThh:mm:ss.sss\"\n";
 print "                      If no time is pointed than current UTC time will be used.\n";
 print "        -ra  RA     - Right Ascension of the source, where RA is in \"hh:mm:ss.sss\"\n";
 print "        -dec DEC    - Declination of the source where DEC is in \"[+\-]dd:mm:ss.sss\"\n";
 print "        -lat PHI    - Latitude in degrees (default - SE607)\n";
 print "        -lon LAMBDA - Longitude in degrees (default - SE607)\n";
 print "                      Western longitudes are negative!\n";
 print "        -site NAME  - Use pre-defined observatory. Following are available: \n";
 print "                      GBT, Arecibo, Parkes, Jodrell, Nancay, Effelsberg, HartRAO,\n";
 print "                      WSRT, LOFAR, DE601, DE602, DE603, DE604, DE605, FR606,\n";
 print "                      SE607, UK608, FI609, PL610, PL611, PL612, UTR2,\n";
 print "                      GMRT, KAT7, MeerKAT, EMBRACE.\n";
 print "        -h          - Print this help.\n";
}

# get current UTC time
sub get_curtime {
 $sec = `date +%S`; chomp $sec;
 $min = `date +%M`; chomp $min;
 $hour = `date +%H`; chomp $hour;
 $day = `date +%d`; chomp $day;
 $month = `date +%m`; chomp $month;
 $year = `date +%Y`; chomp $year;
 $timezone = `date +%z`; chomp $timezone;
 $minadd = $timezone; $minadd =~ s/^[+-]?\d\d(\d\d)$/$1/;
 $houradd = $timezone; $houradd =~ s/^[+-]?(\d\d)\d\d$/$1/;
 if ($timezone =~ /^-/) {
  $min += $minadd;
  if ($min >= 60) { $min -= 60; $hour += 1; }
  $hour += $houradd;
  if ($hour >= 24) { $hour -= 24; $day += 1; }
 } else {
  $min -= $minadd;
  if ($min < 0) { $min += 60; $hour -= 1; }
  $hour -= $houradd;
  if ($hour < 0) { $hour += 24; $day -= 1; }
 }
 $min = sprintf ("%02d", $min);
 $hour = sprintf ("%02d", $hour);
 $day = sprintf ("%02d", $day);
 return "$day.$month.$year $hour:$min:$sec";
}

# unique subroutine to output errors
# one input parameter (string): the error message
sub error {
 my ($error) = @_;
 print "Error: $error\n";
 exit 1;
}

# transform time format into radians
sub time2rad {
 my ($time) = @_;
 $hh = $time; $hh =~ s/^(\d\d)\:.*$/$1/;
 $mm = $time; $mm =~ s/^\d\d\:(\d\d)\:.*$/$1/;
 $ss = $time; $ss =~ s/^\d\d\:\d\d\:(\d\d.*)$/$1/;
 $t = `echo \"scale=20\n($hh + $mm / 60. + $ss / 3600.) * 15. * $rad\" | bc -l`;
 chomp $t;
 return $t;
}

# transform dec format into radians
sub dec2rad {
 my ($d) = @_;
 $deg = $d; $deg =~ s/^([+-]?\d\d)\:.*$/$1/;
 $deg *= 1;
 $mm = $d; $mm =~ s/^[+-]?\d\d\:(\d\d)\:.*$/$1/;
 $ss = $d; $ss =~ s/^[+-]?\d\d\:\d\d\:(\d\d.*)$/$1/;
 if ($deg < 0) {
  $newd = `echo \"scale=20\n($deg - $mm / 60. - $ss / 3600.) * $rad\" | bc -l`;
 } else {
  $newd = `echo \"scale=20\n($deg + $mm / 60. + $ss / 3600.) * $rad\" | bc -l`;
 }
 chomp $newd;
 return $newd;
}

# get hour angle (in rad)
sub get_HA {
 my ($s, $alpha) = @_;
 $srad = &time2rad ($s);
 $alpharad = &time2rad ($alpha);
 $HA = `echo \"scale=20\n$srad - $alpharad\" | bc -l`;
 chomp $HA;
 if ($HA / $rad / 15. < -12.) { $HA += 2.*$pi; }
 if ($HA / $rad / 15. >= 12.) { $HA -= 2.*$pi; }
 return $HA;
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

# converts the date/time from format YYYY-MM-DDTHH:MM:SS.SSS to "DD.MM.YYYY HH:MM:SS.SSS"
sub time_reformat {
 my ($tgiven) = @_;
 $year = $tgiven; $year =~ s/^(\d{4})-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.?\d*$/$1/;
 $month = $tgiven; $month =~ s/^\d{4}-(\d{2})-\d{2}T\d{2}:\d{2}:\d{2}\.?\d*$/$1/;
 $day = $tgiven; $day =~ s/^\d{4}-\d{2}-(\d{2})T\d{2}:\d{2}:\d{2}\.?\d*$/$1/;
 $time = $tgiven; $time =~ s/^\d{4}-\d{2}-\d{2}T(\d{2}:\d{2}:\d{2}\.?\d*)$/$1/;
 return "$day.$month.$year $time";
}

# gets time format string and leaves only 2 decimal digits of seconds
sub time2str {
 my ($time) = @_;
 $tmp = $time;
 $tmp =~ s/^(\d\d\:\d\d\:\d\d\.?\d?\d?).*$/$1/;
 return $tmp;
}
