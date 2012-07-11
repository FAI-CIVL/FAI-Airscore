
DROP database IF EXISTS xcdb;
CREATE database xcdb;
use xcdb;

grant all on xcdb.* to xc@localhost identified by '%MYSQLPASSWORD%';

drop table if exists tblCompetition;
create table tblCompetition
(
    comPk                   integer not null primary key auto_increment, 
    comName                 varchar(100) not null, 
    comLocation             varchar(100) not null, 
    regPk                   integer,
    comDateFrom             DateTime not null,
    comDateTo               DateTime not null,
    comMeetDirName          varchar(100), 
    comContact              varchar(100),
    forPk                   integer, 
    comSanction             varchar(100), 
    comType                 enum ('unknown', 'OLC', 'Free', 'RACE', 'Route', 'Team-RACE' ),
    comCode                 varchar(8),
    comEntryRestrict        enum ('open', 'registered') default 'open',
    comTimeOffset           double default 11.0,
    comOverallScore         enum ('all', 'ftv', 'round') default 'all',
    comOverallParam         double default 0.0,
    comTeamSize             integer default 4,
    comTeamScoring          enum ('aggregate', 'team-gap', 'handicap') default 'aggregate',
    comTeamOver             enum ('best', 'selected') default 'best',
    comClass                enum('PG','HG','mixed')  default 'PG',
    comStyleSheet           varchar(128),
    comLocked               integer default 0
);


drop table if exists tblFormula;
create table tblFormula
(
    forPk            integer not null PRIMARY KEY auto_increment,
    comPk            integer,
    forClass         enum ('gap', 'ozgap', 'pwc', 'sahpa', 'nzl', 'ggap', 'nogap'),
    forVersion       varchar(32),
    forGoalSSpenalty double default 1.0,
    forNomGoal       double default 0.3,
    forMinDistance   double default 5,
    forNomDistance   double default 40,
    forNomTime       double default 90,
    forArrival       enum ('none', 'place', 'timed') default 'place',
    forDeparture     enum ('none', 'departure', 'leadout') default 'leadout',
    forLinearDist    double default 0.5,
    forDiffDist      double default 1.5,
    forDiffRamp      enum ( 'fixed', 'flexible' ) default 'fixed',
    forDiffCalc      enum ( 'all', 'lo' ) default 'all'
);

drop table if exists tblComTaskTrack;
create table tblComTaskTrack
(
    comPk               integer not null,
    tasPk               integer,
    traPk               integer not null,
    index indTrack (traPk)
);

drop table if exists tblTask;
create table tblTask
(
    tasPk                   integer not null primary key auto_increment, 
    comPk                   integer, 
    tasDate                 date not null, 
    tasName                 varchar(100), 
    regPk                   integer,
    tasTaskStart            DateTime,
    tasFinishTime           DateTime, 
    tasLaunchClose          DateTime,
    tasStartTime            DateTime, 
    tasStartCloseTime       DateTime, 
    tasStoppedTime          DateTime, 
    tasFastestTime          integer, 
    tasFirstDepTime         integer, 
    tasFirstArrTime         integer, 
    tasMaxDistance          double, 
    tasResultsType          varchar(20),
    tasTaskType             enum ('free', 'speedrun', 'race', 'olc', 'free-bearing', 'speedrun-interval', 'airgain', 'aat'),
    tasDistance             Double, 
    tasShortRouteDistance   Double, 
    tasSSDistance           Double, 
    tasSSInterval           Integer default 0,
    tasSSOpen               DateTime, 
    tasSSClose              DateTime,
    tasESClose              DateTime,
    tasTotalDistanceFlown   Double,
    tasQuality              Double,
    tasDistQuality          double,
    tasTimeQuality          double,
    tasLaunchQuality        double,                                           
    tasLaunchValid          integer default 1,
    tasPilotsLaunched       integer, 
    tasPilotsTotal          integer,
    tasPilotsES             integer, 
    tasPilotsLO             integer, 
    tasPilotsGoal           integer, 
    tasDeparture            enum ( 'off', 'on', 'leadout' ) default 'on',
    tasArrival              enum ( 'off', 'on' ) default 'on',
    forPk                   integer
);

-- alter table tblTask add column tasTaskStart DateTime;
-- alter table tblTask add column tasStartCloseTime DateTime;
-- update tblTask set tasTaskStart = tasStartTime;

drop table if exists tblTaskWaypoint;
create table tblTaskWaypoint
(
    tawPk           integer not null primary key auto_increment,
    tasPk           integer,
    rwpPk           integer,
    tawNumber       integer not null,
    tawTime         integer,
    tawType         enum ('waypoint', 'start', 'speed', 'endspeed', 'goal') default 'waypoint',
    tawHow          enum ('entry', 'exit') default 'entry',
    tawShape        enum ('circle', 'semicircle', 'line') default 'circle',
    tawAngle        integer,
    tawRadius       integer
);

drop table if exists tblTaskAward;
create table tblTaskAward
(
    tadPk   integer not null primary key auto_increment,
    tawPk   integer,
    traPk   integer,
    tadTime integer
);

drop table if exists tblShortestRoute;
create table tblShortestRoute
(
    tasPk           integer not null,
    tawPk           integer not null,
    ssrLatDecimal   double not null,
    ssrLongDecimal  double not null,
    ssrNumber       integer not null
);

drop table if exists tblGlider;
create table tblGlider
(
    gliPk           integer not null primary key auto_increment,
    gliName         varchar(32),
    gliManufacturer varchar(32),
    gliClass        enum('PG', 'HG') default 'PG',
    gliDHV          enum('1','1/2','2','2/3','competition','floater','kingpost','open','rigid') default 'competition'
    -- class?
);

drop table if exists tblTrack;
create table tblTrack
(
    traPk       integer not null primary key auto_increment,
    pilPk       integer not null,
    witnessPk   integer,
    traClass    enum ('PG', 'HG') default 'PG',
    traGlider   varchar(32),
    traDHV      enum('1','1/2','2','2/3','competition','floater','kingpost','open','rigid') default 'competition',
    traDate     date not null,
    traStart    datetime not null,
    traArea     double,
    traLength   double,
    traScore    double,
    traSafety   enum ('safe', 'maybe', 'unsafe' ) default 'safe',
    traOriginal varchar(128),
    traDuration integer default 0,
    index indPilot (pilPk)
);

drop table if exists tblTaskResult;
create table tblTaskResult
(
    tarPk           integer not null primary key auto_increment,
    tasPk           integer,
    traPk           integer,
    tarDistance     double,
    tarSpeed        double,
    tarStart        integer,
    tarGoal         integer,
    tarResultType   enum ( 'abs', 'dnf', 'lo', 'goal' ) default 'lo',
    tarSS           integer,
    tarES           integer,
    tarTurnpoints   integer,
    tarPenalty      double,
    tarComment      Text,
    tarPlace        integer,
    tarSpeedScore   double,
    tarDistanceScore double,
    tarArrival      double,
    tarDeparture    double,
    tarScore        double,
    tarLeadingCoeff double
);

drop table if exists tblTrackLog;
create table tblTrackLog
(
    traPk           integer not null,
    trlLatDecimal   double not null,
    trlLongDecimal  double not null,
    trlAltitude     integer not null,
    trlTime         integer not null
);

drop table if exists tblBucket;
create table tblBucket
(
    traPk           integer not null,
    bucLatDecimal   double not null,
    bucLongDecimal  double not null,
    bucTime         integer not null
);

drop table if exists tblWaypoint;
create table tblWaypoint
(
    traPk           integer not null,
    wptLatDecimal   double not null,
    wptLongDecimal  double not null,
    wptTime         integer not null,
    wptPosition     integer not null,
    index indTraTime (traPk,wptTime)
);

drop table if exists tblSegment;
create table tblSegment
(
    traPk           integer not null,
    wptLatDecimal   double not null,
    wptLongDecimal  double not null,
    wptTime         integer not null,
    wptPosition     integer not null
);

drop table if exists tblRegion;
create table tblRegion
(
    regPk           integer not null primary key auto_increment,
    regCentre       integer,
    regRadius       double,
    regDescription  varchar(64) not null
);


drop table if exists tblRegionWaypoint;
create table tblRegionWaypoint
(
    rwpPk           integer not null primary key auto_increment,
    regPk           integer,
    rwpName         varchar(12) not null,
    rwpLatDecimal   double not null,
    rwpLongDecimal  double not null,
    rwpAltitude     double not null,
    rwpDescription  varchar(64)
);

insert into tblRegionWaypoint (rwpName,rwpLatDecimal,rwpLongDecimal,rwpAltitude,rwpDescription) values ('mys080', -36.757881, 146.965393, 799, 'Mystic');
insert into tblRegion (regCentre, regDescription) values (1, 'Bright');

drop table if exists tblLaunchSite;
create table tblLaunchSite
(
    lauPk           integer not null primary key auto_increment,
    lauLaunch       varchar(32) not null,
    lauRegion       varchar(32) not null,
    lauLatDecimal   double not null,
    lauLongDecimal  double not null,
    lauAltitude     double not null
);

insert into tblLaunchSite (lauLaunch, lauRegion, lauLatDecimal, lauLongDecimal, lauAltitude) values
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
    ('Pedro Bernardo', 'Spain', 40.2564333333333,-4.90571666666667,1200)
    ;


drop table if exists tblPilot;
create table tblPilot
(
    pilPk           integer not null primary key auto_increment,
    pilFirstName    varchar(40) not null,
    pilLastName     varchar(40) not null,
    pilHGFA         integer not null,
    pilCIVL         integer not null,
    pilSex          enum("M", "F") not null,
    pilValidTo      date,
    pilAddress      varchar(128),
    pilBirthdate    date, 
    pilEmail        varchar(32),
    pilPhoneHome    varchar(24),
    pilPhoneMobile  varchar(24),
    pilYearStarted  varchar(8),
    pilNationCode   varchar(3)
);


drop table if exists tblCompPilot;
create table tblCompPilot
(
    cpiPk           integer not null primary key auto_increment,
    pilPk           integer not null,
    comPk           integer not null,
    cpiRating       enum('restricted', 'intermediate', 'advanced'),
    cpiHours        varchar(8),
    cpiNation       varchar(32),
    cpiState        varchar(32),   
    cpiClub         varchar(32),
    cpiGlider       varchar(32),
    cpiGPS          varchar(32),
    cpiNextOfKin    varchar(128),
    cpiNOKPhone     varchar(32),
    cpiComment      varchar(128) 
);

CREATE TABLE tblUser
(
    usePk       integer not null PRIMARY KEY auto_increment,
    useLogin    varchar(32) not null,
    usePassword varchar(32) not null,
    useEmail    varchar(64)
);

insert into tblUser (useLogin, usePassword) values ('admin', 'admin');

CREATE TABLE tblUserSession
(
    usePk       integer not null,
    useSession  varchar(128),
    useIP       varchar(32),
    useSessTime DateTime,
    useLastTime DateTime
);

CREATE TABLE tblCompAuth
(
    usePk       integer,
    comPk       integer,
    useLevel    enum ( "read", "write", "admin" ) default "read"
);

-- default admin user
insert into tblCompAuth (usePk, comPk, useLevel) values (1,-1,'admin');

CREATE TABLE tblRegionAuth
(
    usePk       integer,
    comPk       integer,
    useLevel    enum ( "read", "write", "admin" ) default "read"
);

-- Airspace stuff ..

drop table if exists tblAirspace;
create table tblAirspace
(
    airPk           integer not null primary key auto_increment,
    airName         varchar(32),
    airClass        enum ( "G", "C", "D", "E", "X" ) default "C",
    airBase         integer,
    airTops         integer,
    airShape        enum ( "circle", "wedge", "polygon" ) default "circle",
    airCentreWP     integer,
    airRadius       float
);

drop table if exists tblAirspaceWaypoint;
create table tblAirspaceWaypoint
(
    awpPk           integer not null primary key auto_increment,
    airPk           integer not null,
    airOrder        integer not null,
    awpConnect      enum ( "line", "arc" ) default "line",
    awpLatDecimal   double not null,
    awpLongDecimal  double not null,
    awpAngleStart   float,
    awpAngleEnd     float,
    awpRadius       float
);

drop table if exists tblTaskAirspace;
create table tblTaskAirspace
(
    taPk            integer not null primary key auto_increment,
    tasPk           integer not null,
    airPk           integer not null
);

-- handicap stuff.
drop table if exists tblHandicap;
create table tblHandicap
(
    hanPk           integer not null primary key auto_increment,
    comPk           integer,
    pilPk           integer,
    hanHandicap     float,
    hanTasks        integer
);


drop table if exists tblPilMap;
create table tblPilMap
(
    pmPk            integer not null primary key auto_increment,
    pilPk           integer,
    ladderPk        integer
);

-- the actual team itself
drop table if exists tblTeam;
create table tblTeam
(
    teaPk               Integer not null PRIMARY KEY auto_increment,
    comPk               integer,
    teaName             varchar(64),
    teaScoring          integer    
);

-- task specific stuff for a team
drop table if exists tblTeamTask;
create table tblTeamTask
(
    tetPk               Integer not null PRIMARY KEY auto_increment,
    tasPk               integer,
    teaPk               integer,
    tetStartGate        datetime
);

-- pilot belonging to a team 
drop table if exists tblTeamPilot;
create table tblTeamPilot
(
    tepPk           Integer not null PRIMARY KEY auto_increment,
    teaPk           integer,
    pilPk           Integer,
    tepPreference   Integer not null default 1, 
    tepModifier     float
);

--DROP TABLE tblTeamScoring;
drop table if exists tblTeamResult;
create table tblTeamResult
(
    terPk           integer not null primary key auto_increment,
    tasPk           integer,
    traPk           integer,
    terDistance     double,
    terSpeed        double,
    terStart        integer,
    terGoal         integer,
    terResultType   enum ( 'abs', 'dnf', 'lo', 'goal' ) default 'lo',
    terSS           integer,
    terES           integer,
    terTurnpoints   integer,
    terPenalty      double,
    terComment      Text,
    terPlace        integer,
    terSpeedScore   double,
    terDistanceScore double,
    terArrival      double,
    terDeparture    double,
    terScore        double,
    terLeadingCoeff double
);

drop table if exists tblRegistration;
create table tblRegistration
(
    regPk           integer not null primary key auto_increment,
    comPk           integer,
    regPaid         integer default 0,
    gliPk           integer,
    pilPk           integer
);

drop table if exists tblTrackMarker;
create table tblTrackMarker
(
    traPk           integer,
    tmDistance      integer,
    tmTime          integer
);

create table schema_version
(
    svKey       varchar(32) not null primary key,
    svWhen      timestamp not null default CURRENT_TIMESTAMP,
    svExtra     varchar(256)
);



