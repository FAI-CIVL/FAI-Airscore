<html>
<body>
<?php
require 'authorisation.php';

$link = db_connect();

$key = 0;

$result = mysqli_query($link, "select svKey from schema_version");
if (mysqli_num_rows($result) > 0)
{
    $key = mysqli_result($result,0);
}

$altarr = [];

$altarr[0] = [
#    "alter table tblCompetition add column comEntryRestrict        enum ('open', 'registered') default 'open'",
#    "alter table tblCompetition add column comLocked        integer default 0",
#    "alter table tblFormula modify column     forClass         enum ('gap', 'ozgap', 'pwc', 'sahpa', 'nzl', 'ggap', 'nogap')",
#    "alter table tblTrack add index indTrack (traPk)",
#    "alter table tblTask modify column tasTaskType             enum ('free', 'speedrun', 'race', 'olc', 'free-bearing', 'speedrun-interval', 'airgain', 'aat')",
#    "alter table tblShortestRoute add column  ssrCumulativeDist  double default 0.0",
#    "alter table tblGlider add column  gliClass        enum('PG', 'HG') default 'PG'",
#    "alter table tblTrack modify column traDHV      enum('1','1/2','2','2/3','competition','floater','kingpost','open','rigid') default 'competition'",
#    "alter table tblTrack add index indPilot (pilPk)",
#    "alter table tblWaypoint add index indTraTime (traPk,wptTime)",
    "alter table tblUserSession modify column useSessTime timestamp default CURRENT_TIMESTAMP",
    "alter table tblUserSession modify column useLastTime timestamp",
    "alter table tblAirspaceWaypoint add column     awpAngleStart   float",
    "alter table tblAirspaceWaypoint add column      awpAngleEnd     float",
    "alter table tblAirspaceWaypoint add column      awpRadius       float",
    "alter table tblRegistration add column gliPk           integer",
    ];

$altarr[1] = [
    'alter table tblFormula add column forStoppedGlideBonus double default 0.0',
    'alter table tblFormula add column forHeightArrBonus double default 0.0',
    'alter table tblFormula add column forHeightArrLower integer default 200',
    'alter table tblFormula add column forHeightArrUpper integer default 3000',
    'alter table tblRegistration add column regHours integer default 200',

];

$altarr[2] = [
    'create table tblAirspaceRegion ( argPk integer not null primary key auto_increment, argRegion varchar(32) not null, argLatDecimal   double not null, argLongDecimal  double not null, argSize integer not null)',
    'alter table tblAirspace modify column airClass enum ( "G", "C", "D", "E", "X", "R", "P", "Q", "W", "GP", "CTR" ) default "C"',
];

$altarr[3] = [
    'alter table tblFormula add column forOLCPoints integer default 3',
    'alter table tblFormula add column forOLCBase double default 1.4'
];

$altarr[4] = [
    'alter table tblTask add column tasComment text'
];

$altarr[5] = [
    'alter table tblFormula add column forDistMeasure   enum ( "average", "median" ) default "average"',
    'alter table tblFormula add column forWeightStart   double default 0.125',
    'alter table tblFormula add column forWeightArrival double default 0.175',
    'alter table tblFormula add column forWeightSpeed   double default 0.7',
    "update tblFormula set forWeightStart=.125 , forWeightArrival=.125, forWeightSpeed=0.75 where forVersion='1998' and forClass='gap'",
    "update tblFormula set forWeightStart=.25  , forWeightArrival=.25,  forWeightSpeed=0.50 where forVersion='2000' and forClass='ozgap'",
    "update tblFormula set forWeightStart=0 ,    forWeightArrival=.25,  forWeightSpeed=0.75 where forVersion='2005' and forClass='ozgap'",
    "update tblFormula set forWeightStart=.175 , forWeightArrival=.25,  forWeightSpeed=0.575 where forVersion not in ('2000','2005') and forClass='ozgap'",
    "update tblFormula set forWeightStart=0.0 ,  forWeightArrival=0.0,  forWeightSpeed=1.0 where forClass in ('nzl', 'jtgap', 'rtgap', 'nogap')"
];

mysqli_query($link, 'delete from schema_version');
mysqli_query($link, "insert into schema_version (svKey, svExtra) values (5, 'dbup')");

for ($i = $key; $i < length($altarr); $i++)
{
    foreach ($altarr[$i] as $row)
    {
        $result = mysqli_query($link, $row) or die('Error ' . mysqli_errno($link) . ' Alter failed: ' . mysqli_connect_error());
    }
}
 
if ($key < 1)
{
    $query = "create table schema_version
    (
        svKey       varchar(32) not null primary key,
        svWhen      timestamp not null default CURRENT_TIMESTAMP,
        svExtra     varchar(256)
    )";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Schema failed: ' . mysqli_connect_error());
}

if ($key < 5)
{
    $query = "create table tblLaunchSite (
    lauPk           integer not null primary key auto_increment,
    lauLaunch       varchar(32) not null,
    lauRegion       varchar(32) not null,
    lauLatDecimal   double not null,
    lauLongDecimal  double not null,
    lauAltitude     double not null
    )";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' LaunchSite failed: ' . mysqli_connect_error());

    $query = "insert into tblLaunchSite (lauLaunch, lauRegion, lauLatDecimal, lauLongDecimal, lauAltitude) values
    ('Chelan', 'USA',47.8061,-120.041683333333,1200),
    ('Tiger Mtn', 'USA', 47.50145, -121.988533333333, 800),
    ('Woodrat', 'USA', 42.2314666666667, -123.003816666667, 1200),
    ('Blackheath', 'NSW', -33.64365, 150.244516666667, 1000),
    ('Balmoral', 'Queensland', -26.7583333333333,  152.8924, 420),
    ('Middle Brother', 'NSW', -31.7032666666667,152.681133333333, 450),
    ('Killarney', 'Queensland', -28.2948166666667, 152.34165, 940),
    ('Toowoomba', 'Queensland', -27.4599833333333, 151.8462, 600),
    ('Veslea', 'Norway', 59.6192333333333, 8.69566666666667, 620),
    ('Laragne', 'France', 44.2968333333333, 5.76273333333333, 1320),
    ('St Vincent Les Forts', 'France', 44.447116666666, 6.37201666666667, 1200),
    ('Manteigas', 'Portugal', 40.4026166666667,-7.45433333333333, 800),
    ('Ager', 'Spain', 42.0459833333333 ,0.745933333333333, 1530),
    ('Valle de Bravo', 'Mexico', 19.0616, -100.090116666667, 2340),
    ('Bayramoren', 'Turkey', 40.9710333333333,33.2099, 1280),
    ('Bir', 'India', 32.0598166666667,76.7444333333333, 2400),
    ('Piedrahita', 'Spain', 40.4220333333333, -5.30106666666667, 1900),
    ('Ivanhoe', 'NSW', -32.883,144.3111, 100),
    ('Stanwell Park', 'NSW', -34.2233833333333, 150.99925, 140),
    ('Paeroa', 'New Zealand', -38.37825,176.255166666667, 800),
    ('Nelson', 'New Zealand',-41.3435833333333,173.250316666667,500),
    ('Wanaka', 'New Zealand',-44.7732,169.384433333333,1000),
    ('Mystic','Victoria',-36.7578811646,146.965393066,800),
    ('Beechmont','Queensland',-28.118194,153.201639,530),
    ('Mt Broughton','Victoria',-37.1230963549893,145.413665771484,650),
    ('Conargo', 'Victoria', -35.318,145.170, 100),
    ('Manilla','NSW',-30.6766853333,150.610824585,860),
    ('Mt Lonarch', 'Victoria',-37.2584833333333,143.3397,600),
    ('Mt Elliot','Victoria',-36.186035,147.974553,940),
    ('Annecy','France',45.81405,6.24851666666667,900),
    ('Mt Tamborine','Queensland',-27.950278,153.181194,548),
    ('Pedro Bernardo', 'Spain', 40.2564333333333,-4.90571666666667,1200)";

 
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' insert launch failed: ' . mysqli_connect_error());
}


echo "<h1>Updated DB to verion: $key</h1>";

?>
</body>
</html>

