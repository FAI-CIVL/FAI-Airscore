
use xcdb;

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

