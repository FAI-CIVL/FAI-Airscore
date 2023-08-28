# coding: utf-8
from sqlalchemy import (
    CHAR,
    TIMESTAMP,
    func,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Table,
    Text,
    text,
)
from sqlalchemy.dialects.mysql import (
    INTEGER,
    NUMERIC,
    FLOAT,
    LONGTEXT,
    MEDIUMINT,
    SMALLINT,
    TINYINT,
    VARCHAR,
)
from sqlalchemy.orm import aliased, relationship

from .conn import db_session
from .models import BaseModel, metadata

# Created using sqlacodegen library
# sqlacodegen mysql+pymysql://user:pwd@server/database --outfile db_tables_new.py


class CompObjectView(BaseModel):
    __table__ = Table(
        'CompObjectView',
        metadata,
        Column('comp_id', INTEGER(11), primary_key=True),
        Column('comp_name', String(100)),
        Column('comp_site', String(100)),
        Column('date_from', Date),
        Column('date_to', Date),
        Column('MD_name', String(100)),
        Column('contact', String(100)),
        Column('sanction', String(20), server_default=text("'none'")),
        Column('comp_type', Enum('RACE', 'Route', 'Team-RACE'), server_default=text("'RACE'")),
        Column('comp_code', String(8)),
        Column('restricted', TINYINT(1), server_default=text("'1'")),
        Column('time_offset', MEDIUMINT(9), server_default=text("'0'")),
        Column('comp_class', Enum('PG', 'HG', 'mixed'), server_default=text("'PG'")),
        Column('openair_file', String(40)),
        Column('stylesheet', String(128)),
        Column('locked', TINYINT(1), server_default=text("'0'")),
        Column('comp_path', String(40)),
        Column('external', INTEGER(2), server_default=text("'0'")),
        Column('website', String(100)),
        Column('airspace_check', TINYINT(1)),
        Column('check_launch', Enum('on', 'off'), server_default=text("'off'")),
        Column('igc_config_file', String(80)),
        Column('self_register', TINYINT(1), server_default=text("'0'")),
        Column('track_source', String(40)),
        Column('formula_name', String(50)),
        Column('overall_validity', Enum('ftv', 'all', 'round'), server_default=text("'ftv'")),
        Column('validity_param', NUMERIC(precision=4, asdecimal=False), server_default=text("'0.750'")),
        Column('validity_ref', Enum('day_quality', 'max_score'), server_default=text("'max_score'")),
        Column('nominal_goal', NUMERIC(precision=3, asdecimal=False), server_default=text("'0.30'")),
        Column('min_dist', MEDIUMINT(9), server_default=text("'5000'")),
        Column('nominal_dist', MEDIUMINT(9), server_default=text("'45000'")),
        Column('nominal_time', SMALLINT(6), server_default=text("'5400'")),
        Column('nominal_launch', NUMERIC(precision=3, asdecimal=False), server_default=text("'0.96'")),
        Column('formula_distance', Enum('on', 'difficulty', 'off'), server_default=text("'on'")),
        Column('formula_arrival', Enum('position', 'time', 'off'), server_default=text("'off'")),
        Column('formula_departure', Enum('leadout', 'departure', 'off'), server_default=text("'leadout'")),
        Column('lead_factor', NUMERIC(precision=4, asdecimal=False)),
        Column('formula_time', Enum('on', 'off'), server_default=text("'on'")),
        Column('no_goal_penalty', NUMERIC(precision=4, asdecimal=False), server_default=text("'1.000'")),
        Column('glide_bonus', NUMERIC(precision=4, asdecimal=False), server_default=text("'4.00'")),
        Column('tolerance', NUMERIC(precision=6, asdecimal=False), server_default=text("'0.10000'")),
        Column('min_tolerance', INTEGER(4), server_default=text("'5'")),
        Column('arr_alt_bonus', FLOAT, server_default=text("'0'")),
        Column('arr_min_height', SMALLINT(6)),
        Column('arr_max_height', SMALLINT(6)),
        Column('validity_min_time', SMALLINT(6)),
        Column('score_back_time', SMALLINT(6), server_default=text("'300'")),
        Column('max_JTG', SMALLINT(6), server_default=text("'0'")),
        Column('JTG_penalty_per_sec', NUMERIC(precision=4, asdecimal=False)),
        Column('scoring_altitude', Enum('GPS', 'QNH'), server_default=text("'GPS'")),
        Column('task_result_decimal', INTEGER(2), server_default=text("'0'")),
        Column('comp_result_decimal', INTEGER(2), server_default=text("'0'")),
        Column('team_scoring', TINYINT(1), server_default=text("'0'")),
        Column('team_size', INTEGER(4)),
        Column('max_team_size', INTEGER(4)),
        Column('country_scoring', TINYINT(1), server_default=text("'0'")),
        Column('country_size', INTEGER(4)),
        Column('max_country_size', INTEGER(4)),
        Column('team_over', INTEGER(2)),
        Column('check_g_record', Boolean),
    )


class TaskFormulaView(BaseModel):
    __table__ = Table(
        'TaskFormulaView',
        metadata,
        Column('task_id', INTEGER(11), primary_key=True),
        Column('comp_id', INTEGER(11), index=True),
        Column('formula_name', String(50)),
        Column('comp_class', Enum('PG', 'HG', 'mixed'), server_default=text("'PG'")),
        Column('overall_validity', Enum('ftv', 'all', 'round'), server_default=text("'ftv'")),
        Column('validity_param', NUMERIC(precision=4, asdecimal=False), server_default=text("'0.750'")),
        Column('validity_ref', Enum('day_quality', 'max_score'), server_default=text("'max_score'")),
        Column('nominal_goal', NUMERIC(precision=3, asdecimal=False), server_default=text("'0.30'")),
        Column('min_dist', MEDIUMINT(9), server_default=text("'5000'")),
        Column('nominal_dist', MEDIUMINT(9), server_default=text("'45000'")),
        Column('nominal_time', SMALLINT(6), server_default=text("'5400'")),
        Column('nominal_launch', NUMERIC(precision=3, asdecimal=False), server_default=text("'0.96'")),
        Column('formula_distance', Enum('on', 'difficulty', 'off')),
        Column('formula_departure', Enum('leadout', 'departure', 'off')),
        Column('formula_arrival', Enum('position', 'time', 'off')),
        Column('formula_time', Enum('on', 'off')),
        Column('lead_factor', NUMERIC(precision=4, asdecimal=False)),
        Column('no_goal_penalty', NUMERIC(precision=4, asdecimal=False)),
        Column('glide_bonus', NUMERIC(precision=4, asdecimal=False), server_default=text("'4.00'")),
        Column('tolerance', NUMERIC(precision=6, asdecimal=False)),
        Column('min_tolerance', INTEGER(4), server_default=text("'5'")),
        Column('arr_alt_bonus', FLOAT),
        Column('arr_min_height', SMALLINT(6)),
        Column('arr_max_height', SMALLINT(6)),
        Column('validity_min_time', SMALLINT(6)),
        Column('score_back_time', SMALLINT(6), server_default=text("'300'")),
        Column('max_JTG', SMALLINT(6)),
        Column('JTG_penalty_per_sec', NUMERIC(precision=4, asdecimal=False)),
        Column('scoring_altitude', Enum('GPS', 'QNH'), server_default=text("'GPS'")),
        Column('task_result_decimal', INTEGER(4)),
        Column('team_scoring', TINYINT(1)),
        Column('team_size', INTEGER(4)),
        Column('max_team_size', INTEGER(4)),
        Column('country_scoring', TINYINT(1)),
        Column('country_size', INTEGER(4)),
        Column('max_country_size', INTEGER(4)),
    )


class FlightResultView(BaseModel):
    __table__ = Table(
        'FlightResultView',
        metadata,
        Column('track_id', INTEGER(11), primary_key=True),
        Column('par_id', INTEGER(11)),
        Column('task_id', INTEGER(11)),
        Column('comp_id', INTEGER(11)),
        Column('civl_id', INTEGER(10)),
        Column('fai_id', String(20)),
        Column('pil_id', INTEGER(11)),
        Column('ID', INTEGER(4)),
        Column('name', String(50)),
        Column('sex', Enum('M', 'F'), server_default=text("'M'")),
        Column('nat', CHAR(10)),
        Column('glider', String(100)),
        Column('glider_cert', String(20)),
        Column('sponsor', String(500)),
        Column('team', String(100)),
        Column('nat_team', TINYINT(4), server_default=text("'1'")),
        Column('live_id', String(10)),
        Column('best_dist_to_ESS', FLOAT),
        Column('distance_flown', FLOAT),
        Column('best_distance_time', MEDIUMINT(9), nullable=False, server_default=text("'0'")),
        Column('stopped_distance', FLOAT),
        Column('stopped_altitude', SMALLINT(6), server_default=text("'0'")),
        Column('total_distance', FLOAT),
        Column('speed', FLOAT),
        Column('first_time', MEDIUMINT(9)),
        Column('real_start_time', MEDIUMINT(9)),
        Column('goal_time', MEDIUMINT(9)),
        Column('last_time', MEDIUMINT(9)),
        Column('result_type', String(7)),
        Column('SSS_time', MEDIUMINT(9)),
        Column('ESS_time', MEDIUMINT(9)),
        Column('waypoints_made', INTEGER(11)),
        Column('penalty', FLOAT),
        Column('comment', Text),
        Column('fixed_LC', FLOAT),
        Column('ESS_altitude', SMALLINT(6), server_default=text("'0'")),
        Column('goal_altitude', SMALLINT(6)),
        Column('max_altitude', SMALLINT(6), server_default=text("'0'")),
        Column('last_altitude', SMALLINT(6)),
        Column('landing_altitude', SMALLINT(6)),
        Column('landing_time', MEDIUMINT(9)),
        Column('track_file', String(255)),
        Column('g_record', TINYINT(4)),
    )


class PilotView(BaseModel):
    __table__ = Table(
        'Pilots',
        metadata,
        Column('pil_id', INTEGER(11), primary_key=True),
        Column('login', String(60)),
        Column('pwd', String(255)),
        Column('email', String(100)),
        Column('first_name', LONGTEXT),
        Column('last_name', LONGTEXT),
        Column('nat', LONGTEXT),
        Column('phone', LONGTEXT),
        Column('sex', String(1)),
        Column('glider_brand', LONGTEXT),
        Column('glider', LONGTEXT),
        Column('glider_cert', LONGTEXT),
        Column('glider_class', String(12)),
        Column('sponsor', LONGTEXT),
        Column('fai_id', LONGTEXT),
        Column('civl_id', LONGTEXT),
        Column('livetrack24_id', LONGTEXT),
        Column('airtribune_id', LONGTEXT),
        Column('xcontest_id', LONGTEXT),
        Column('telegram_id', INTEGER(11)),
    )


class User(BaseModel):
    __table__ = Table(
        'users',
        metadata,
        Column('id', INTEGER(11), primary_key=True),
        Column('username', String(60)),
        Column('password', String(255)),
        Column('email', String(100)),
        Column('created_at', DateTime),
        Column('first_name', LONGTEXT),
        Column('last_name', LONGTEXT),
        Column('nat', LONGTEXT),
        Column('phone', LONGTEXT),
        Column('sex', String(1)),
        Column('active', TINYINT(1)),
        Column('access', Enum('pilot', 'scorekeeper', 'manager', 'admin', 'pending')),
    )


class RegionWaypointView(BaseModel):
    __table__ = Table(
        'RegionWaypointView',
        metadata,
        Column('rwp_id', INTEGER(11), primary_key=True),
        Column('region_id', INTEGER(11)),
        Column('name', String(12)),
        Column('lat', NUMERIC(precision=8, asdecimal=False)),
        Column('lon', NUMERIC(precision=9, asdecimal=False)),
        Column('altitude', SMALLINT(6)),
        Column('description', String(64)),
    )


class TaskObjectView(BaseModel):
    __table__ = Table(
        'TaskObjectView',
        metadata,
        Column('task_id', INTEGER(11), primary_key=True),
        Column('comp_code', String(8)),
        Column('comp_name', String(100)),
        Column('comp_site', String(100)),
        Column('time_offset', MEDIUMINT(9), server_default=text("'0'")),
        Column('comp_class', Enum('PG', 'HG', 'mixed'), server_default=text("'PG'")),
        Column('comp_id', INTEGER(11)),
        Column('date', Date),
        Column('task_name', String(100)),
        Column('task_num', TINYINT(4)),
        Column('reg_id', INTEGER(11)),
        Column('training', TINYINT(1), server_default=text("'0'")),
        Column('region_name', String(40)),
        Column('window_open_time', MEDIUMINT(9)),
        Column('task_deadline', MEDIUMINT(9)),
        Column('window_close_time', MEDIUMINT(9)),
        Column('check_launch', Enum('on', 'off'), server_default=text("'off'")),
        Column('start_time', MEDIUMINT(9)),
        Column('SS_interval', SMALLINT(6), server_default=text("'0'")),
        Column('start_iteration', TINYINT(4)),
        Column('start_close_time', MEDIUMINT(9)),
        Column('stopped_time', MEDIUMINT(9)),
        Column('task_type', String(21)),
        Column('distance', FLOAT),
        Column('opt_dist', FLOAT),
        Column('opt_dist_to_SS', FLOAT),
        Column('opt_dist_to_ESS', FLOAT),
        Column('SS_distance', FLOAT),
        Column('QNH', NUMERIC(precision=7, asdecimal=False), server_default=text("'1013.250'")),
        Column('comment', Text),
        Column('locked', TINYINT(3), server_default=text("'0'")),
        Column('airspace_check', TINYINT(1)),
        Column('openair_file', String(40)),
        Column('cancelled', TINYINT(1), server_default=text("'0'")),
        Column('track_source', String(40)),
        Column('task_path', String(40)),
        Column('comp_path', String(40)),
        Column('igc_config_file', String(80)),
    )


class UnscoredPilotView(BaseModel):
    __table__ = Table(
        'UnscoredPilotView',
        metadata,
        Column('task_id', INTEGER(11)),
        Column('par_id', INTEGER(11), primary_key=True),
        Column('comp_id', INTEGER(11)),
        Column('civl_id', INTEGER(10)),
        Column('fai_id', String(20)),
        Column('pil_id', INTEGER(11)),
        Column('ID', INTEGER(4)),
        Column('name', String(50)),
        Column('sex', Enum('M', 'F'), server_default=text("'M'")),
        Column('nat', CHAR(10)),
        Column('glider', String(100)),
        Column('glider_cert', String(20)),
        Column('xcontest_id', String(20)),
        Column('live_id', String(10)),
        Column('sponsor', String(500)),
        Column('team', String(100)),
        Column('nat_team', TINYINT(4), server_default=text("'1'")),
    )


class TrackObjectView(BaseModel):
    __table__ = Table(
        'TrackObjectView',
        metadata,
        Column('track_id', INTEGER(11), primary_key=True),
        Column('par_id', INTEGER(11)),
        Column('task_id', INTEGER(11)),
        Column('civl_id', INTEGER(10)),
        Column('glider', String(100)),
        Column('glider_cert', String(20)),
        Column('track_file', String(255)),
    )


schema_version = Table(
    'schema_version',
    metadata,
    Column('svKey', INTEGER(11), nullable=False, server_default=text("'0'")),
    Column('svWhen', TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP")),
    Column('svExtra', String(256)),
)


class TblCertification(BaseModel):
    __tablename__ = 'tblCertification'

    cert_id = Column(INTEGER(11), primary_key=True, autoincrement=True)
    cert_name = Column(String(15), nullable=False)
    comp_class = Column(Enum('PG', 'HG', 'mixed'), nullable=False, server_default=text("'PG'"))
    cert_order = Column(TINYINT(1), nullable=False)


class TblCountryCode(BaseModel):
    __tablename__ = 'tblCountryCode'

    natName = Column(String(52), nullable=False)
    natIso2 = Column(String(2), nullable=False)
    natIso3 = Column(String(3), nullable=False)
    natId = Column(INTEGER(11), primary_key=True)
    natIoc = Column(String(3))
    natRegion = Column(String(8))
    natSubRegion = Column(String(25))
    natRegionId = Column(INTEGER(11))
    natSubRegionId = Column(INTEGER(11))

    @classmethod
    def get_list(cls, countries: set = None, iso: int = None) -> list:
        """ returns a list of dict"""
        CC = aliased(cls)
        column = getattr(CC, 'natIoc') if not iso else getattr(CC, 'natIso' + str(iso))
        with db_session() as db:
            print(f'session id: {id(db)}')
            query = db.query(CC.natName.label('name'), column.label('code')).filter(column.isnot(None))
            if countries:
                query = query.filter(column.in_(countries))
            results = query.order_by(CC.natName).all()
            return [el._asdict() for el in results]


class TblForComp(BaseModel):
    __tablename__ = 'tblForComp'

    comp_id = Column(INTEGER(11), ForeignKey('tblCompetition.comp_id'), primary_key=True)
    last_update = Column(TIMESTAMP, nullable=False,
                         server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    formula_name = Column(String(20))
    overall_validity = Column(Enum('ftv', 'all', 'round'), nullable=False, server_default=text("'ftv'"))
    validity_param = Column(NUMERIC(precision=4, asdecimal=False), nullable=False, server_default=text("'0.75'"))
    validity_ref = Column(Enum('day_quality', 'max_score'), server_default=text("'max_score'"))
    nominal_goal = Column(NUMERIC(precision=3, asdecimal=False), nullable=False, server_default=text("'0.3'"))
    min_dist = Column(MEDIUMINT(9), nullable=False, server_default=text("'5000'"))
    nominal_dist = Column(MEDIUMINT(9), nullable=False, server_default=text("'45000'"))
    nominal_time = Column(SMALLINT(6), nullable=False, server_default=text("'5400'"))
    nominal_launch = Column(NUMERIC(precision=4, asdecimal=False), nullable=False, server_default=text("'0.96'"))
    formula_distance = Column(Enum('on', 'difficulty', 'off'), nullable=False, server_default=text("'on'"))
    formula_arrival = Column(Enum('position', 'time', 'off'), nullable=False, server_default=text("'off'"))
    formula_departure = Column(Enum('leadout', 'departure', 'off'), nullable=False, server_default=text("'leadout'"))
    lead_factor = Column(NUMERIC(precision=4, asdecimal=False))
    formula_time = Column(Enum('on', 'off'), nullable=False, server_default=text("'on'"))
    no_goal_penalty = Column(NUMERIC(precision=4, asdecimal=False), nullable=False, server_default=text("'1'"))
    glide_bonus = Column(NUMERIC(precision=4, asdecimal=False), nullable=False, server_default=text("'4'"))
    tolerance = Column(NUMERIC(precision=6, asdecimal=False), nullable=False, server_default=text("'0.1'"))
    min_tolerance = Column(INTEGER(4), nullable=False, server_default=text("'5'"))
    arr_alt_bonus = Column(FLOAT, nullable=False, server_default=text("'0'"))
    arr_min_height = Column(SMALLINT(6))
    arr_max_height = Column(SMALLINT(6))
    validity_min_time = Column(SMALLINT(6))
    score_back_time = Column(SMALLINT(6), nullable=False, server_default=text("'300'"))
    max_JTG = Column(SMALLINT(6), nullable=False, server_default=text("'0'"))
    JTG_penalty_per_sec = Column(NUMERIC(precision=4, asdecimal=False))
    scoring_altitude = Column(Enum('GPS', 'QNH'), nullable=False, server_default=text("'GPS'"))
    task_result_decimal = Column(INTEGER(2), nullable=False, server_default=text("'0'"))
    comp_result_decimal = Column(INTEGER(2), nullable=False, server_default=text("'0'"))
    team_scoring = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    team_size = Column(INTEGER(4))
    max_team_size = Column(INTEGER(4))
    country_scoring = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    country_size = Column(INTEGER(4))
    max_country_size = Column(INTEGER(4))
    team_over = Column(INTEGER(2))


class TblLadder(BaseModel):
    __tablename__ = 'tblLadder'

    ladder_id = Column(INTEGER(11), primary_key=True, autoincrement=True)
    ladder_name = Column(String(100), nullable=False)
    ladder_class = Column(Enum('PG', 'HG'), nullable=False, server_default=text("'PG'"))
    nat = Column(String(10))
    date_from = Column(Date)
    date_to = Column(Date)
    external = Column(TINYINT(1), server_default=text("'0'"))


class TblParticipant(BaseModel):
    __tablename__ = 'tblParticipant'
    __table_args__ = (Index('par_pil_id', 'pil_id', 'comp_id'),)

    par_id = Column(INTEGER(11), primary_key=True, autoincrement=True)
    comp_id = Column(INTEGER(11), ForeignKey('tblCompetition.comp_id'), index=True)
    civl_id = Column(INTEGER(10), index=True)
    pil_id = Column(INTEGER(11))
    ID = Column(INTEGER(4))
    name = Column(String(100))
    birthdate = Column(Date)
    sex = Column(Enum('M', 'F'), nullable=False, server_default=text("'M'"))
    nat = Column(CHAR(10))
    glider = Column(String(100))
    glider_cert = Column(String(20))
    sponsor = Column(String(500))
    fai_valid = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    fai_id = Column(String(20))
    xcontest_id = Column(String(20))
    live_id = Column(String(10))
    telegram_id = Column(INTEGER(11))
    team = Column(String(100))
    nat_team = Column(TINYINT(4), nullable=False, server_default=text("'1'"))
    status = Column(Enum('confirmed', 'wild card', 'waiting list', 'cancelled', 'waiting for payment'))
    ranking = Column(MEDIUMINT(9))
    paid = Column(TINYINT(1), server_default=text("'0'"))
    hours = Column(SMALLINT(6))
    child_par_attr = relationship(
        "TblParticipantMeta", back_populates="parent_par",
        cascade="all, delete",
        passive_deletes=True
    )

    @classmethod
    def get_dicts(cls, comp_id: int) -> list:
        """ returns a list of rows"""
        P = aliased(cls)
        with db_session() as db:
            print(f'session id: {id(db)}')
            return [el.as_dict() for el in db.query(P).filter_by(comp_id=comp_id).all()]


class TblRegion(BaseModel):
    __tablename__ = 'tblRegion'

    reg_id = Column(INTEGER(11), primary_key=True, autoincrement=True)
    comp_id = Column(INTEGER(11))
    centre = Column(INTEGER(11))
    radius = Column(FLOAT)
    description = Column(String(64), nullable=False)
    waypoint_file = Column(String(50), nullable=False)
    openair_file = Column(String(50))


class TblResultFile(BaseModel):
    __tablename__ = 'tblResultFile'
    __table_args__ = (Index('ref_id', 'filename'),)

    ref_id = Column(INTEGER(11), primary_key=True, autoincrement=True)
    comp_id = Column(INTEGER(11), nullable=False)
    task_id = Column(INTEGER(11))
    created = Column(INTEGER(11), nullable=False)
    filename = Column(VARCHAR(80), index=True)
    status = Column(VARCHAR(255))
    active = Column(TINYINT(1), nullable=False, server_default=text("'0'"))


TblUserSession = Table(
    'tblUserSession',
    metadata,
    Column('user_id', INTEGER(11), nullable=False),
    Column('user_session', String(128)),
    Column('user_IP', String(32)),
    Column('session_start', TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP")),
    Column('session_end', TIMESTAMP, nullable=False, server_default=text("'0000-00-00 00:00:00'")),
)


class TblXContestCode(BaseModel):
    __tablename__ = 'tblXContestCodes'

    xccSiteID = Column(INTEGER(11))
    xccSiteName = Column(String(40))
    xccToID = Column(INTEGER(11), primary_key=True)
    xccToName = Column(String(40), nullable=False)
    xccAlt = Column(INTEGER(11))
    xccISO = Column(String(2), nullable=False)
    xccCountryName = Column(String(42))


class TblCompetition(BaseModel):
    __tablename__ = 'tblCompetition'
    __table_args__ = (Index('comp_id', 'comp_id', 'comp_name', unique=True),)

    comp_id = Column(INTEGER(11), primary_key=True, autoincrement=True)
    comp_name = Column(String(100), nullable=False)
    comp_code = Column(String(8))
    comp_class = Column(Enum('PG', 'HG', 'mixed'), server_default=text("'PG'"))
    last_update = Column(
        TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    )
    comp_site = Column(String(100), nullable=False)
    date_from = Column(Date, nullable=False)
    date_to = Column(Date, nullable=False)
    time_offset = Column(MEDIUMINT(9), nullable=False, server_default=text("'0'"))
    MD_name = Column(String(100))
    contact = Column(String(100))
    sanction = Column(String(20), nullable=False, server_default=text("'none'"))
    openair_file = Column(String(40))
    comp_type = Column(Enum('RACE', 'Route', 'Team-RACE'), server_default=text("'RACE'"))
    restricted = Column(TINYINT(1), server_default=text("'1'"))
    track_source = Column(String(40))
    stylesheet = Column(String(128))
    locked = Column(TINYINT(1), server_default=text("'0'"))
    external = Column(INTEGER(2), nullable=False, server_default=text("'0'"))
    website = Column(String(100))
    comp_path = Column(String(40))
    airspace_check = Column(TINYINT(1))
    check_launch = Column(Enum('on', 'off'), server_default=text("'off'"))
    igc_config_file = Column(String(80))
    self_register = Column(TINYINT(1))
    check_g_record = Column(Boolean)

    ladders = relationship('TblLadder', secondary='tblLadderComp')
    child_comp_attr = relationship(
        "TblCompAttribute", back_populates="parent_comp",
        cascade="all, delete",
        passive_deletes=True
    )
    child_comp_check = relationship(
        "TblAirspaceCheck", back_populates="parent_comp_check",
        cascade="all, delete",
        passive_deletes=True
    )


class TblCompAuth(BaseModel):
    __tablename__ = 'tblCompAuth'

    user_id = Column(INTEGER(11), primary_key=True)
    comp_id = Column(INTEGER(11), ForeignKey("tblCompetition.comp_id"), primary_key=True)
    user_auth = Column(Enum('read', 'write', 'admin', 'owner'), nullable=False, server_default=text("'read'"))
    comp = relationship(TblCompetition, backref='Auth')


class TblCompAttribute(BaseModel):
    __tablename__ = 'tblCompAttribute'

    attr_id = Column(INTEGER(11), primary_key=True, autoincrement=True)
    comp_id = Column(INTEGER(11), ForeignKey("tblCompetition.comp_id"), nullable=False)
    attr_key = Column(String(100), nullable=False)
    attr_value = Column(String(100), nullable=True)
    comp = relationship(TblCompetition, backref='CompAttr')
    child_attr = relationship(
        "TblParticipantMeta", back_populates="parent_comp_attr",
        cascade="all, delete",
        passive_deletes=True
    )
    parent_comp = relationship('TblCompetition', back_populates="child_comp_attr")


class TblCompRanking(BaseModel):
    __tablename__ = 'tblCompRanking'

    rank_id = Column(INTEGER(11), primary_key=True, autoincrement=True)
    comp_id = Column(INTEGER(11), ForeignKey("tblCompetition.comp_id"), nullable=False)
    rank_name = Column(String(40), nullable=False)
    rank_type = Column(String(40), nullable=False, server_default=text("'cert'"))
    cert_id = Column(INTEGER(11), ForeignKey("tblCertification.cert_id"), nullable=True)
    min_date = Column(Date)
    max_date = Column(Date)
    attr_id = Column(INTEGER(11), ForeignKey("tblCompAttribute.attr_id"), nullable=True)
    rank_value = Column(String(100))
    comp = relationship('TblCompetition')
    cert = relationship('TblCertification')
    attr = relationship('TblCompAttribute')


class TblParticipantMeta(BaseModel):
    __tablename__ = 'tblParticipantMeta'

    pat_id = Column(INTEGER(11), primary_key=True, autoincrement=True)
    par_id = Column(INTEGER(11), ForeignKey("tblParticipant.par_id", ondelete="CASCADE"), nullable=False)
    attr_id = Column(INTEGER(11), ForeignKey("tblCompAttribute.attr_id", ondelete="CASCADE"), nullable=False)
    meta_value = Column(String(100))
    parent_par = relationship('TblParticipant', back_populates='child_par_attr')
    parent_comp_attr = relationship('TblCompAttribute', back_populates="child_attr")


class TblLadderRanking(BaseModel):
    __tablename__ = 'tblLadderRanking'

    rank_id = Column(INTEGER(11), primary_key=True, autoincrement=True)
    ladder_id = Column(INTEGER(11), ForeignKey("tblLadder.ladder_id"), nullable=False)
    rank_name = Column(String(40), nullable=False)
    rank_type = Column(String(40), nullable=False, server_default=text("'cert'"))
    cert_id = Column(INTEGER(11), ForeignKey("tblCertification.cert_id"), nullable=True)
    min_date = Column(Date)
    max_date = Column(Date)
    rank_key = Column(String(100))
    rank_value = Column(String(100))
    ladder = relationship('TblLadder')
    ladder_cert = relationship('TblCertification')


class TblLadderSeason(BaseModel):
    __tablename__ = 'tblLadderSeason'

    ladder_id = Column(ForeignKey('tblLadder.ladder_id'), nullable=False, index=True, primary_key=True)
    season = Column(INTEGER(6), nullable=False, index=True)
    active = Column(TINYINT(1), server_default=text("'1'"))
    overall_validity = Column(Enum('all', 'ftv', 'round'), nullable=False, server_default=text("'ftv'"))
    validity_param = Column(NUMERIC(precision=4, asdecimal=False), nullable=False)


TblRegionXCSites = Table(
    'tblRegionXCSites',
    metadata,
    Column('reg_id', ForeignKey('tblRegion.reg_id', ondelete='CASCADE'), nullable=False, index=True),
    Column('xccSiteID', INTEGER(11), nullable=False, index=True),
)


class TblAirspaceCheck(BaseModel):
    __tablename__ = 'tblAirspaceCheck'

    check_id = Column(INTEGER(11), primary_key=True, autoincrement=True)
    comp_id = Column(ForeignKey('tblCompetition.comp_id', ondelete='CASCADE'), nullable=False)
    task_id = Column(INTEGER(11), ForeignKey("tblTask.task_id", ondelete='CASCADE'), nullable=True)
    notification_distance = Column(SMALLINT(4), nullable=False, server_default=text("'100'"))
    function = Column(Enum('linear', 'non-linear'), nullable=False, server_default=text("'linear'"))
    h_outer_limit = Column(SMALLINT(4), nullable=False, server_default=text("'70'"))
    h_boundary = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    h_boundary_penalty = Column(NUMERIC(precision=3, asdecimal=False), nullable=False, server_default=text("'0.1'"))
    h_inner_limit = Column(SMALLINT(4), nullable=False, server_default=text("'-30'"))
    h_max_penalty = Column(NUMERIC(precision=3, asdecimal=False), nullable=False, server_default=text("'1'"))
    v_outer_limit = Column(SMALLINT(4), nullable=False, server_default=text("'70'"))
    v_boundary = Column(SMALLINT(4), nullable=False, server_default=text("'0'"))
    v_boundary_penalty = Column(NUMERIC(precision=3, asdecimal=False), nullable=False, server_default=text("'0.1'"))
    v_inner_limit = Column(SMALLINT(4), nullable=False, server_default=text("'-30'"))
    v_max_penalty = Column(NUMERIC(precision=3, asdecimal=False), nullable=False, server_default=text("'1'"))

    parent_comp_check = relationship('TblCompetition', back_populates='child_comp_check')
    parent_task_check = relationship('TblTask', back_populates="child_task_check")


class TblLadderComp(BaseModel):
    __tablename__ = 'tblLadderComp'

    ladder_id = Column(ForeignKey('tblLadder.ladder_id', ondelete='CASCADE'), index=True)
    comp_id = Column(ForeignKey('tblCompetition.comp_id', ondelete='CASCADE'), primary_key=True, index=True)


class TblRegionWaypoint(BaseModel):
    __tablename__ = 'tblRegionWaypoint'

    rwp_id = Column(INTEGER(11), primary_key=True, autoincrement=True)
    reg_id = Column(ForeignKey('tblRegion.reg_id'), index=True)
    name = Column(String(12), nullable=False)
    lat = Column(NUMERIC(precision=8, asdecimal=False), nullable=False)
    lon = Column(NUMERIC(precision=9, asdecimal=False), nullable=False)
    altitude = Column(SMALLINT(6), nullable=False)
    description = Column(String(64))
    old = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    xccSiteID = Column(INTEGER(11))
    xccToID = Column(INTEGER(11))

    reg = relationship('TblRegion')


class TblTask(BaseModel):
    __tablename__ = 'tblTask'

    task_id = Column(INTEGER(11), primary_key=True, autoincrement=True)
    comp_id = Column(ForeignKey('tblCompetition.comp_id'), index=True)
    last_update = Column(
        TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    )
    task_num = Column(TINYINT(4), nullable=False)
    task_name = Column(String(100))
    date = Column(Date, nullable=False)
    reg_id = Column(ForeignKey('tblRegion.reg_id'), index=True)
    training = Column(TINYINT(1), server_default=text("'0'"))
    window_open_time = Column(MEDIUMINT(9))
    window_close_time = Column(MEDIUMINT(9))
    check_launch = Column(Enum('on', 'off'), server_default=text("'off'"))
    start_time = Column(MEDIUMINT(9))
    start_close_time = Column(MEDIUMINT(9))
    SS_interval = Column(SMALLINT(6), nullable=False, server_default=text("'0'"))
    start_iteration = Column(TINYINT(4))
    task_deadline = Column(MEDIUMINT(9))
    stopped_time = Column(MEDIUMINT(9))
    task_type = Column(
        Enum('race', 'elapsed time', 'free distance', 'distance with bearing'), server_default=text("'race'")
    )
    distance = Column(FLOAT)
    opt_dist = Column(FLOAT)
    opt_dist_to_SS = Column(FLOAT)
    opt_dist_to_ESS = Column(FLOAT)
    SS_distance = Column(FLOAT)
    cancelled = Column(TINYINT(1), server_default=text("'0'"))
    time_offset = Column(MEDIUMINT(9))
    formula_distance = Column(Enum('on', 'difficulty', 'off'))
    formula_departure = Column(Enum('leadout', 'departure', 'off'))
    formula_arrival = Column(Enum('position', 'time', 'off'))
    formula_time = Column(Enum('on', 'off'))
    arr_alt_bonus = Column(FLOAT)
    max_JTG = Column(SMALLINT(6))
    no_goal_penalty = Column(NUMERIC(precision=4, asdecimal=False))
    tolerance = Column(NUMERIC(precision=6, asdecimal=False))
    airspace_check = Column(TINYINT(1))
    openair_file = Column(String(40))
    QNH = Column(NUMERIC(precision=7, asdecimal=False), nullable=False, server_default=text("'1013.25'"))
    comment = Column(Text)
    locked = Column(TINYINT(3), nullable=False, server_default=text("'0'"))
    task_path = Column(String(40))

    reg = relationship('TblRegion')
    comp = relationship('TblCompetition')
    Results = relationship('TblTaskResult')
    child_task_check = relationship(
        "TblAirspaceCheck", back_populates="parent_task_check",
        cascade="all, delete",
        passive_deletes=True
    )


class TblTaskResult(BaseModel):
    __tablename__ = 'tblTaskResult'
    __table_args__ = (Index('track_id', 'task_id', 'par_id', unique=True),)

    track_id = Column(INTEGER(11), primary_key=True, autoincrement=True)
    task_id = Column(ForeignKey('tblTask.task_id', ondelete='SET NULL'), index=True)
    par_id = Column(INTEGER(11), ForeignKey('tblParticipant.par_id'), index=True)
    last_update = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    track_file = Column(String(255))
    g_record = Column(TINYINT(4), server_default=text("'1'"))
    best_dist_to_ESS = Column(FLOAT)
    distance_flown = Column(FLOAT)
    best_distance_time = Column(MEDIUMINT(9), nullable=False, server_default=text("'0'"))
    stopped_distance = Column(FLOAT)
    stopped_altitude = Column(SMALLINT(6), nullable=False, server_default=text("'0'"))
    total_distance = Column(FLOAT)
    first_time = Column(MEDIUMINT(9), nullable=False, server_default=text("'0'"))
    real_start_time = Column(MEDIUMINT(9), nullable=False, server_default=text("'0'"))
    SSS_time = Column(MEDIUMINT(9), nullable=False, server_default=text("'0'"))
    ESS_time = Column(MEDIUMINT(9), nullable=False, server_default=text("'0'"))
    goal_time = Column(MEDIUMINT(9), nullable=False, server_default=text("'0'"))
    last_time = Column(MEDIUMINT(9), nullable=False, server_default=text("'0'"))
    speed = Column(FLOAT)
    waypoints_made = Column(TINYINT(4))
    ESS_altitude = Column(SMALLINT(6), nullable=False, server_default=text("'0'"))
    goal_altitude = Column(SMALLINT(6), nullable=False, server_default=text("'0'"))
    max_altitude = Column(SMALLINT(6), nullable=False, server_default=text("'0'"))
    last_altitude = Column(SMALLINT(6), server_default=text("'0'"))
    landing_time = Column(MEDIUMINT(9), nullable=False, server_default=text("'0'"))
    landing_altitude = Column(SMALLINT(6), nullable=False, server_default=text("'0'"))
    result_type = Column(Enum('abs', 'dnf', 'lo', 'goal', 'mindist', 'nyp'), server_default=text("'nyp'"))
    penalty = Column(FLOAT)
    comment = Column(Text)
    place = Column(SMALLINT(6))
    distance_score = Column(FLOAT)
    time_score = Column(FLOAT)
    arrival_score = Column(FLOAT)
    departure_score = Column(FLOAT)
    score = Column(FLOAT)
    lead_coeff = Column(FLOAT)
    fixed_LC = Column(FLOAT)

    # Participants = relationship('TblParticipant', backref="taskresults", lazy="subquery")
    Participants = relationship('TblParticipant')

    @classmethod
    def get_task_results(cls, task_id: int) -> list:
        p = aliased(TblParticipant)
        t = aliased(TblTask)
        with db_session() as db:
            objects = (
                db.query(
                    cls.track_id,
                    p.par_id,
                    t.task_id,
                    p.comp_id,
                    p.civl_id,
                    p.fai_id,
                    p.pil_id,
                    p.ID,
                    p.name,
                    p.nat,
                    p.sex,
                    p.birthdate,
                    p.glider,
                    p.glider_cert,
                    p.sponsor,
                    p.team,
                    p.nat_team,
                    p.live_id,
                    cls.best_dist_to_ESS,
                    cls.distance_flown,
                    cls.best_distance_time,
                    cls.stopped_distance,
                    cls.stopped_altitude,
                    cls.total_distance,
                    cls.speed,
                    cls.first_time,
                    cls.real_start_time,
                    cls.goal_time,
                    cls.last_time,
                    cls.result_type,
                    cls.SSS_time,
                    cls.ESS_time,
                    cls.waypoints_made,
                    cls.penalty,
                    cls.comment,
                    cls.time_score,
                    cls.distance_score,
                    cls.arrival_score,
                    cls.departure_score,
                    cls.score,
                    cls.lead_coeff,
                    cls.fixed_LC,
                    cls.ESS_altitude,
                    cls.goal_altitude,
                    cls.max_altitude,
                    cls.last_altitude,
                    cls.landing_altitude,
                    cls.landing_time,
                    cls.track_file,
                    cls.g_record,
                )
                .join(t, t.comp_id == p.comp_id)
                .outerjoin(cls, (cls.task_id == t.task_id) & (cls.par_id == p.par_id))
                .filter(t.task_id == task_id)
            )
            return objects.all()

    @classmethod
    def get_task_flights(cls, task_id: int) -> list:
        p = aliased(TblParticipant)
        t = aliased(TblTask)
        with db_session() as db:
            objects = (
                db.query(
                    cls.track_id,
                    cls.par_id,
                    cls.task_id,
                    p.comp_id,
                    p.civl_id,
                    p.fai_id,
                    p.pil_id,
                    p.ID,
                    p.name,
                    p.nat,
                    p.sex,
                    p.glider,
                    p.glider_cert,
                    p.sponsor,
                    p.team,
                    p.nat_team,
                    p.live_id,
                    cls.distance_flown,
                    cls.best_distance_time,
                    cls.stopped_distance,
                    cls.stopped_altitude,
                    cls.total_distance,
                    cls.speed,
                    cls.first_time,
                    cls.real_start_time,
                    cls.goal_time,
                    cls.last_time,
                    cls.result_type,
                    cls.SSS_time,
                    cls.ESS_time,
                    cls.waypoints_made,
                    cls.penalty,
                    cls.comment,
                    cls.time_score,
                    cls.distance_score,
                    cls.arrival_score,
                    cls.departure_score,
                    cls.score,
                    cls.lead_coeff,
                    cls.fixed_LC,
                    cls.ESS_altitude,
                    cls.goal_altitude,
                    cls.max_altitude,
                    cls.last_altitude,
                    cls.landing_altitude,
                    cls.landing_time,
                    cls.track_file,
                    cls.g_record,
                )
                .join(t, t.comp_id == p.comp_id)
                .outerjoin(cls, (cls.task_id == t.task_id) & (cls.par_id == p.par_id))
                .filter(t.task_id == task_id)
            )
            return objects.filter(cls.result_type.in_(['lo', 'goal'])).all()


class TblNotification(BaseModel):
    __tablename__ = 'tblNotification'

    not_id = Column(INTEGER(11), primary_key=True)
    track_id = Column(INTEGER(11), nullable=False, index=True)
    notification_type = Column(
        Enum('custom', 'track', 'jtg', 'auto'), nullable=False, server_default=text("'custom'")
    )
    flat_penalty = Column(NUMERIC(precision=8, asdecimal=False), nullable=False, server_default=text("'0.0000'"))
    percentage_penalty = Column(NUMERIC(precision=5, asdecimal=False), nullable=False, server_default=text("'0.0000'"))
    comment = Column(String(80))

    @classmethod
    def from_track_list(cls, ids: list) -> list:
        with db_session() as db:
            return db.query(cls).filter(cls.track_id.in_(ids)).all()


class TblTaskWaypoint(BaseModel):
    __tablename__ = 'tblTaskWaypoint'

    wpt_id = Column(INTEGER(11), primary_key=True, autoincrement=True)
    task_id = Column(ForeignKey('tblTask.task_id', ondelete='SET NULL'), index=True)
    last_update = Column(TIMESTAMP, nullable=False,
                         server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    num = Column(TINYINT(4), nullable=False)
    name = Column(CHAR(6), nullable=False)
    rwp_id = Column(INTEGER(11))
    lat = Column(NUMERIC(precision=8, asdecimal=False), nullable=False)
    lon = Column(NUMERIC(precision=9, asdecimal=False), nullable=False)
    altitude = Column(SMALLINT(6), nullable=False, server_default=text("'0'"))
    description = Column(String(80))
    time = Column(MEDIUMINT(9))
    type = Column(
        Enum('waypoint', 'launch', 'speed', 'endspeed', 'goal'), index=True, server_default=text("'waypoint'")
    )
    how = Column(Enum('entry', 'exit'), server_default=text("'entry'"))
    shape = Column(Enum('circle', 'semicircle', 'line'), server_default=text("'circle'"))
    angle = Column(SMALLINT(6))
    radius = Column(MEDIUMINT(9))
    ssr_lat = Column(NUMERIC(precision=8, asdecimal=False))
    ssr_lon = Column(NUMERIC(precision=9, asdecimal=False))
    partial_distance = Column(FLOAT)

    task = relationship('TblTask')

    @classmethod
    def from_task_id(cls, task_id: int) -> list:
        """ returns a list of rows"""
        W = aliased(cls)
        with db_session() as db:
            print(f'session id: {id(db)}')
            return db.query(W).filter_by(task_id=task_id).order_by(W.num).all()


class TblTrackWaypoint(BaseModel):
    __tablename__ = 'tblTrackWaypoint'
    __table_args__ = (Index('track_id'),)

    trw_id = Column(INTEGER(11), primary_key=True)
    track_id = Column(INTEGER(11), nullable=False, index=True)
    wpt_id = Column(INTEGER(11))
    name = Column(String(10))
    rawtime = Column(MEDIUMINT(9), nullable=False)
    lat = Column(NUMERIC(precision=8, asdecimal=False), nullable=False)
    lon = Column(NUMERIC(precision=9, asdecimal=False), nullable=False)
    altitude = Column(SMALLINT(6), nullable=False)

    @classmethod
    def from_track_list(cls, ids: list) -> list:
        with db_session() as db:
            return db.query(cls).filter(cls.track_id.in_(ids)).all()

    @classmethod
    def from_track(cls, track_id: int) -> list:
        with db_session() as db:
            return db.query(cls).filter_by(track_id=track_id).all()

    @classmethod
    def get_dict_list(cls, ids: list) -> list:
        with db_session() as db:
            return [el.as_dict() for el in db.query(cls).filter(cls.track_id.in_(ids)).all()]
