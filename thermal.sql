

create table tblThermal
(
    thmClimbRate    double not null, 
    thmLatApprox    double not null,
    thmLongApprox   double not null
);

create temporary table ThermalTrack
(
    thmID           integer not null primary key auto_increment,
    traPk           integer not null,
    trlLatDecimal   double not null,
    trlLongDecimal  double not null,
    trlAltitude     integer not null,
    trlTime         integer not null
);

insert into ThermalTrack
select * from tblTrackLog 
--where
--    trlLatDecimal between () and 
--    trlLongDecimal between () 
order by traPk, trlTime

insert into tblThermal (thmClimbRate,thmLatApprox,thmLongApprox)
select sum((B.alt - A.alt)/(B.trlTime - A.trlTime))/count(*) as thmClimbRate,
    round(A.latDecimal,3) as thmLatApprox, 
    round(A.longDecimal,3) as thmLongApprox
from #TT A, #TT B 
where A.id = B.id+1
    group by thmLatApprox, thmLongApprox
    

Transparent tiles on overlaid on google map of size XX,XX
red +ve  ..
blue -ve ..

