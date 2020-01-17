# coding: utf-8
from sqlalchemy import BINARY, CHAR, Column, DECIMAL, Date, DateTime, Enum, Float, ForeignKey, PrimaryKeyConstraint, \
    Index, String, TIMESTAMP, Table, Text, text
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, LONGTEXT, MEDIUMTEXT, SMALLINT, TINYINT, VARCHAR
from sqlalchemy.orm import relationship
from myconn import Base, metadata


class CompResultView(Base):
    __table__ = Table('CompResultView', metadata,

                      Column('comp_id', INTEGER(11), primary_key=True),
                      Column('comp_name', String(100)),
                      Column('comp_site', String(100)),
                      Column('date_from', String(10)),
                      Column('date_to', String(10)),
                      Column('MD_name', String(100)),
                      Column('contact', String(100)),
                      Column('sanction', Enum('FAI 1', 'League', 'PWC', 'FAI 2', 'none'),
                             server_default=text("'none'")),
                      Column('type', Enum('RACE', 'Route', 'Team-RACE'), server_default=text("'RACE'")),
                      Column('comp_code', String(8)),
                      Column('restricted', Enum('open', 'registered'), server_default=text("'registered'")),
                      Column('time_offset', Float(asdecimal=False)),
                      Column('comp_class', Enum('PG', 'HG', 'mixed'), server_default=text("'PG'")),
                      Column('website', String(100)),
                      Column('formula', String(88)),
                      Column('formula_type', Enum('gap', 'pwc', 'RTG'), server_default=text("'pwc'")),
                      Column('team_size', INTEGER(4), server_default=text("'0'")),
                      Column('overall_validity', Enum('ftv', 'all', 'round'), server_default=text("'ftv'")),
                      Column('validity_param', Float, server_default=text("'0.75'")),
                      Column('team_scoring', TINYINT(1), server_default=text("'0'")),
                      Column('country_scoring', TINYINT(1), server_default=text("'0'")),
                      Column('team_over', INTEGER(2))
                      )


class CompFormulaView(Base):
    __table__ = Table('CompFormulaView', metadata,
                      Column('forPk', INTEGER(11)),
                      Column('comp_id', INTEGER(11), primary_key=True),
                      Column('comp_class', Enum('PG', 'HG', 'mixed'), server_default=text("'PG'")),
                      Column('formula_type', String(10)),
                      Column('formula_version', INTEGER(8)),
                      Column('formula_name', String(50)),
                      Column('overall_validity', Enum('ftv', 'all', 'round'), server_default=text("'ftv'")),
                      Column('validity_param', Float, server_default=text("'0.75'")),
                      Column('nominal_goal', Float, server_default=text("'0.3'")),
                      Column('min_dist', Float(asdecimal=False), server_default=text("'0'")),
                      Column('nominal_dist', Float(asdecimal=False), server_default=text("'0'")),
                      Column('nominal_time', Float(asdecimal=False), server_default=text("'0'")),
                      Column('nominal_launch', Float, server_default=text("'0.96'")),
                      Column('formula_distance', Enum('on', 'difficulty', 'off'), server_default=text("'on'")),
                      Column('formula_arrival', Enum('position', 'time', 'off'), server_default=text("'off'")),
                      Column('formula_departure', Enum('leadout', 'departure', 'off'),
                             server_default=text("'leadout'")),
                      Column('lead_factor', Float),
                      Column('formula_time', Enum('on', 'off'), server_default=text("'on'")),
                      Column('no_goal_penalty', Float, server_default=text("'1'")),
                      Column('glide_bonus', Float, server_default=text("'4'")),
                      Column('tolerance', Float),
                      Column('min_tolerance', INTEGER(4)),
                      Column('arr_alt_bonus', Float, server_default=text("'0'")),
                      Column('arr_min_height', INTEGER(11)),
                      Column('arr_max_height', INTEGER(11)),
                      Column('validity_min_time', BIGINT(13)),
                      Column('score_back_time', BIGINT(13), server_default=text("'0'")),
                      Column('max_JTG', SMALLINT(6)),
                      Column('JTG_penalty_per_sec', Float),
                      Column('scoring_altitude', Enum('GPS', 'QNH'), nullable=False, server_default=text("'GPS'"))
                      )


class CompetitionView(Base):
    __table__ = Table('CompetitionView', metadata,

                      Column('comPk', INTEGER(11), primary_key=True),
                      Column('comName', String(100)),
                      Column('comLocation', String(100)),
                      Column('comDateFrom', DateTime),
                      Column('comDateTo', DateTime),
                      Column('comMeetDirName', String(100)),
                      Column('comContact', String(100)),
                      Column('claPk', INTEGER(11), server_default=text("'0'")),
                      Column('comSanction', Enum('FAI 1', 'League', 'PWC', 'FAI 2', 'none'),
                             server_default=text("'none'")),
                      Column('comType', Enum('RACE', 'Route', 'Team-RACE'), server_default=text("'RACE'")),
                      Column('comCode', String(8)),
                      Column('comEntryRestrict', Enum('open', 'registered'), server_default=text("'registered'")),
                      Column('comTimeOffset', Float(asdecimal=False), server_default=text("'11'")),
                      Column('comClass', Enum('PG', 'HG', 'mixed'), server_default=text("'PG'")),
                      Column('comOpenAirFile', String(40)),
                      Column('comStyleSheet', String(128)),
                      Column('comLocked', INTEGER(11), server_default=text("'0'")),
                      Column('comPath', String(80)),
                      Column('comExt', INTEGER(2), server_default=text("'0'")),
                      Column('comExtUrl', String(100)),
                      Column('forName', String(50)),
                      Column('comOverallScore', Enum('ftv', 'all', 'round'), server_default=text("'ftv'")),
                      Column('comOverallParam', Float(asdecimal=False), server_default=text("'0.75'")),
                      Column('forNomGoal', Float(asdecimal=False), server_default=text("'0.3'")),
                      Column('forMinDistance', Float(asdecimal=False), server_default=text("'5'")),
                      Column('forNomDistance', Float(asdecimal=False), server_default=text("'45'")),
                      Column('forNomTime', Float(asdecimal=False), server_default=text("'90'")),
                      Column('forNomLaunch', Float(asdecimal=False), server_default=text("'0.96'")),
                      Column('forScorebackTime', INTEGER(11), server_default=text("'5'")),
                      Column('comTeamSize', INTEGER(11)),
                      Column('comTeamScoring', Enum('off', 'on'), server_default=text("'off'")),
                      Column('comTeamOver', INTEGER(2)),
                      Column('forPk', BIGINT(11)),
                      Column('forClass', String(3)),
                      Column('forVersion', String(32)),
                      Column('forComClass', String(5))
                      )


class CompObjectView(Base):
    __table__ = Table('CompObjectView', metadata,

                      Column('comp_id', INTEGER(11), primary_key=True),
                      Column('comp_name', String(100)),
                      Column('comp_site', String(100)),
                      Column('date_from', Date),
                      Column('date_to', Date),
                      Column('MD_name', String(100)),
                      Column('contact', String(100)),
                      Column('cat_id', INTEGER(11), server_default=text("'0'")),
                      Column('sanction', Enum('FAI 1', 'League', 'PWC', 'FAI 2', 'none'),
                             server_default=text("'none'")),
                      Column('comp_type', Enum('RACE', 'Route', 'Team-RACE'), server_default=text("'RACE'")),
                      Column('comp_code', String(8)),
                      Column('restricted', Enum('open', 'registered'), server_default=text("'registered'")),
                      Column('time_offset', Float(asdecimal=False), server_default=text("'11'")),
                      Column('comp_class', Enum('PG', 'HG', 'mixed'), server_default=text("'PG'")),
                      Column('openair_file', String(40)),
                      Column('stylesheet', String(128)),
                      Column('locked', INTEGER(11), server_default=text("'0'")),
                      Column('comp_path', String(80)),
                      Column('external', INTEGER(2), server_default=text("'0'")),
                      Column('website', String(100)),
                      Column('formula_type', String(10)),
                      Column('formula_version', INTEGER(8)),
                      Column('formula_name', String(50)),
                      Column('overall_validity', Enum('ftv', 'all', 'round'), server_default=text("'ftv'")),
                      Column('validity_param', Float, server_default=text("'0.75'")),
                      Column('nominal_goal', Float, server_default=text("'0.3'")),
                      Column('min_dist', Float(asdecimal=False), server_default=text("'0'")),
                      Column('nominal_dist', Float(asdecimal=False), server_default=text("'0'")),
                      Column('nominal_time', Float(asdecimal=False), server_default=text("'0'")),
                      Column('nominal_launch', Float, server_default=text("'0.96'")),
                      Column('formula_distance', Enum('on', 'difficulty', 'off'), server_default=text("'on'")),
                      Column('formula_arrival', Enum('position', 'time', 'off'), server_default=text("'off'")),
                      Column('formula_departure', Enum('leadout', 'departure', 'off'),
                             server_default=text("'leadout'")),
                      Column('lead_factor', Float),
                      Column('formula_time', Enum('on', 'off'), server_default=text("'on'")),
                      Column('no_goal_penalty', Float, server_default=text("'1'")),
                      Column('glide_bonus', Float, server_default=text("'4'")),
                      Column('tolerance', Float),
                      Column('min_tolerance', INTEGER(4)),
                      Column('arr_alt_bonus', Float, server_default=text("'0'")),
                      Column('arr_min_height', INTEGER(11)),
                      Column('arr_max_height', INTEGER(11)),
                      Column('validity_min_time', BIGINT(13)),
                      Column('score_back_time', BIGINT(13), server_default=text("'0'")),
                      Column('max_JTG', SMALLINT(6)),
                      Column('JTG_penalty_per_sec', Float),
                      Column('scoring_altitude', Enum('GPS', 'QNH'), nullable=False, server_default=text("'GPS'")),
                      Column('team_size', INTEGER(11)),
                      Column('team_scoring', TINYINT(1), server_default=text("'0'")),
                      Column('team_over', INTEGER(2)),
                      Column('country_scoring', TINYINT(1), server_default=text("'0'"))
                      )


class PilotView(Base):
    __table__ = Table('PilotView', metadata,

                      Column('pilPk', BIGINT(20), primary_key=True),
                      Column('pilLogin', String(60)),
                      Column('pilpass', String(255)),
                      Column('pilEmail', String(100)),
                      Column('pilFirstName', LONGTEXT),
                      Column('pilLastName', LONGTEXT),
                      Column('pilNat', LONGTEXT),
                      Column('pilPhoneMobile', LONGTEXT),
                      Column('pilSex', String(1)),
                      Column('pilGliderBrand', LONGTEXT),
                      Column('pilGlider', LONGTEXT),
                      Column('gliGliderCert', LONGTEXT),
                      Column('gliGliderClass', String(12)),
                      Column('pilSponsor', LONGTEXT),
                      Column('pilFAI', LONGTEXT),
                      Column('pilCIVL', LONGTEXT),
                      Column('pilLT24User', LONGTEXT),
                      Column('pilATUser', LONGTEXT),
                      Column('pilXContestUser', LONGTEXT)
                      )


class RegionWaypointView(Base):
    __table__ = Table('RegionWaypointView', metadata,

                      Column('rwpPk', INTEGER(11), primary_key=True),
                      Column('region_id', INTEGER(11)),
                      Column('name', String(12)),
                      Column('lat', Float(asdecimal=False)),
                      Column('lon', Float(asdecimal=False)),
                      Column('altitude', INTEGER(11)),
                      Column('description', String(64))
                      )


class RegistrationView(Base):
    __table__ = Table('RegistrationView', metadata,

                      Column('par_id', INTEGER(11), primary_key=True),
                      Column('comp_id', INTEGER(11)),
                      Column('civl_id', INTEGER(10)),
                      Column('pil_id', INTEGER(11)),
                      Column('ID', INTEGER(4)),
                      Column('name', String(50)),
                      Column('birthdate', CHAR(10)),
                      Column('sex', Enum('M', 'F'), server_default=text("'M'")),
                      Column('female', INTEGER(1), server_default=text("'0'")),
                      Column('nat', CHAR(10)),
                      Column('glider', String(100)),
                      Column('glider_cert', String(20)),
                      Column('sponsor', String(100)),
                      Column('fai_valid', TINYINT(1), server_default=text("'1'")),
                      Column('fai_id', String(20)),
                      Column('xcontest_id', String(20)),
                      Column('live_id', String(10)),
                      Column('team', String(100)),
                      Column('nat_team', TINYINT(4), server_default=text("'1'")),
                      Column('status',
                             Enum('confirmed', 'wild card', 'waiting list', 'cancelled', 'waiting for payment')),
                      Column('ranking', INTEGER(11)),
                      Column('paid', INTEGER(11), server_default=text("'0'"))
                      )


class RegisteredPilotView(Base):
    __table__ = Table('RegisteredPilotView', metadata,

                      Column('par_id', INTEGER(11), primary_key=True),
                      Column('comp_id', INTEGER(11)),
                      Column('civl_id', INTEGER(10)),
                      Column('fai_id', String(20)),
                      Column('pil_id', INTEGER(11)),
                      Column('ID', INTEGER(4)),
                      Column('name', String(50)),
                      Column('sex', Enum('M', 'F'), server_default=text("'M'")),
                      Column('birthdate', CHAR(10)),
                      Column('nat', CHAR(10)),
                      Column('glider', String(100)),
                      Column('glider_cert', String(20)),
                      Column('sponsor', String(100)),
                      Column('xcontest_id', CHAR(20)),
                      Column('live_id', CHAR(10)),
                      Column('team', String(100)),
                      Column('nat_team', TINYINT(4), server_default=text("'1'")),
                      Column('status',
                             Enum('confirmed', 'wild card', 'waiting list', 'cancelled', 'waiting for payment')),
                      Column('ranking', INTEGER(11)),

                      )


class UnscoredPilotView(Base):
    __table__ = Table('UnscoredPilotView', metadata,

                      Column('task_id', INTEGER(11), primary_key=True),
                      Column('par_id', INTEGER(11)),
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
                      Column('sponsor', String(100)),
                      Column('team', String(100)),
                      Column('nat_team', TINYINT(4), server_default=text("'1'"))
                      )


class ResultView(Base):
    __table__ = Table('ResultView', metadata,

                      Column('tarPk', INTEGER(11), primary_key=True),
                      Column('parPk', INTEGER(11)),
                      Column('tasPk', INTEGER(11)),
                      Column('pilPk', INTEGER(11)),
                      Column('pilName', LONGTEXT),
                      Column('pilSponsor', LONGTEXT),
                      Column('pilNationCode', String(10)),
                      Column('pilSex', String(1)),
                      Column('traGlider', String(100)),
                      Column('traDHV', String(20)),
                      Column('tarDistance', Float(asdecimal=False)),
                      Column('tarSpeed', Float(asdecimal=False)),
                      Column('tarStart', INTEGER(11)),
                      Column('tarGoal', INTEGER(11)),
                      Column('tarResultType', String(7)),
                      Column('tarSS', INTEGER(11)),
                      Column('tarES', INTEGER(11)),
                      Column('tarTurnpoints', INTEGER(11)),
                      Column('tarPenalty', Float(asdecimal=False)),
                      Column('tarComment', Text),
                      Column('tarPlace', INTEGER(11)),
                      Column('tarSpeedScore', Float(asdecimal=False)),
                      Column('tarDistanceScore', Float(asdecimal=False)),
                      Column('tarArrivalScore', Float(asdecimal=False)),
                      Column('tarDepartureScore', Float(asdecimal=False)),
                      Column('tarScore', Float(asdecimal=False)),
                      Column('tarLeadingCoeff', Float(asdecimal=False)),
                      Column('tarFixedLC', Float(asdecimal=False)),
                      Column('tarLastAltitude', INTEGER(11)),
                      Column('tarLastTime', INTEGER(11))
                      )


class TaskFormulaView(Base):
    __table__ = Table('TaskFormulaView', metadata,

                      Column('task_id', INTEGER(11), primary_key=True),
                      Column('formula_type', String(10)),
                      Column('formula_version', INTEGER(8)),
                      Column('formula_name', String(50)),
                      Column('nominal_goal', Float, server_default=text("'0.3'")),
                      Column('min_dist', Float(asdecimal=False), server_default=text("'0'")),
                      Column('nominal_dist', Float(asdecimal=False), server_default=text("'0'")),
                      Column('nominal_time', Float(asdecimal=False), server_default=text("'0'")),
                      Column('nominal_launch', Float, server_default=text("'0.96'")),
                      Column('formula_distance', String(10)),
                      Column('formula_departure', String(9)),
                      Column('formula_arrival', String(8)),
                      Column('formula_time', String(3)),
                      Column('lead_factor', Float),
                      Column('no_goal_penalty', Float(20, False), server_default=text("'0.000'")),
                      Column('glide_bonus', Float, server_default=text("'4'")),
                      Column('tolerance', Float(21, False)),
                      Column('min_tolerance', INTEGER(4)),
                      Column('arr_alt_bonus', Float(asdecimal=False), server_default=text("'0'")),
                      Column('arr_min_height', INTEGER(11)),
                      Column('arr_max_height', INTEGER(11)),
                      Column('validity_min_time', BIGINT(13)),
                      Column('score_back_time', BIGINT(13), server_default=text("'0'")),
                      Column('max_JTG', SMALLINT(6)),
                      Column('JTG_penalty_per_sec', Float),
                      Column('scoring_altitude', Enum('GPS', 'QNH'), server_default=text("'GPS'"))
                      )


class TaskObjectView(Base):
    __table__ = Table('TaskObjectView', metadata,

                      Column('task_id', INTEGER(11), primary_key=True),
                      Column('comp_code', String(8)),
                      Column('comp_name', String(100)),
                      Column('comp_site', String(100)),
                      Column('time_offset', BIGINT(21)),
                      Column('comp_class', Enum('PG', 'HG', 'mixed'), server_default=text("'PG'")),
                      Column('comp_id', INTEGER(11)),
                      Column('date', Date, nullable=False),
                      Column('task_name', String(100)),
                      Column('task_num', TINYINT(3)),
                      Column('reg_id', INTEGER(11)),
                      Column('window_open_time', BIGINT(21)),
                      Column('task_deadline', BIGINT(21)),
                      Column('window_close_time', BIGINT(21)),
                      Column('check_launch', Enum('on', 'off'), server_default=text("'off'")),
                      Column('start_time', BIGINT(21)),
                      Column('start_iteration', SMALLINT(6)),
                      Column('SS_interval', BIGINT(13)),
                      Column('start_close_time', BIGINT(21)),
                      Column('stopped_time', BIGINT(21)),
                      Column('task_type', String(21)),
                      Column('distance', Float(asdecimal=False)),
                      Column('opt_dist', Float(asdecimal=False)),
                      Column('opt_dist_to_SS', Float(asdecimal=False)),
                      Column('opt_dist_to_ESS', Float(asdecimal=False)),
                      Column('SS_distance', Float(asdecimal=False)),
                      Column('comment', Text),
                      Column('locked', TINYINT(3), server_default=text("'0'")),
                      Column('launch_valid', BIGINT(11)),
                      Column('airspace_check', TINYINT(1)),
                      Column('openair_file', String(40)),
                      Column('track_source', String(40)),
                      Column('task_path', String(40)),
                      Column('comp_path', String(40))
                      )


class FlightResultView(Base):
    __table__ = Table('FlightResultView', metadata,

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
                      Column('sponsor', String(100)),
                      Column('team', String(100)),
                      Column('nat_team', TINYINT(4), server_default=text("'1'")),
                      Column('distance_flown', Float(asdecimal=False)),
                      Column('speed', Float(asdecimal=False)),
                      Column('first_time', INTEGER(11)),
                      Column('real_start_time', INTEGER(11)),
                      Column('goal_time', INTEGER(11)),
                      Column('last_time', INTEGER(11)),
                      Column('result_type', String(7)),
                      Column('SSS_time', INTEGER(11)),
                      Column('ESS_time', INTEGER(11)),
                      Column('best_waypoint_achieved', INTEGER(11)),
                      Column('penalty', Float(asdecimal=False)),
                      Column('comment', Text),
                      Column('fixed_LC', Float(asdecimal=False)),
                      Column('ESS_altitude', INTEGER(11), server_default=text("'0'")),
                      Column('goal_altitude', INTEGER(11)),
                      Column('max_altitude', INTEGER(11), server_default=text("'0'")),
                      Column('last_altitude', INTEGER(11)),
                      Column('landing_altitude', INTEGER(11)),
                      Column('landing_time', INTEGER(11)),
                      Column('track_file', String(255)),
                      Column('g_record', TINYINT(4))
                      )


class TaskResultView(Base):
    __table__ = Table('TaskResultView', metadata,

                      Column('track_id', INTEGER(11), primary_key=True),
                      Column('par_id', INTEGER(11)),
                      Column('task_id', INTEGER(11)),
                      Column('pil_id', INTEGER(11)),
                      Column('civl_id', INTEGER(10)),
                      Column('fai_id', String(20)),
                      Column('ID', INTEGER(4)),
                      Column('name', String(50)),
                      Column('sponsor', String(100)),
                      Column('nat', CHAR(10)),
                      Column('sex', Enum('M', 'F'), server_default=text("'M'")),
                      Column('glider', String(100)),
                      Column('glider_cert', String(20)),
                      Column('team', String(80)),
                      Column('nat_team', TINYINT(4), server_default=text("'1'")),
                      Column('distance', Float(asdecimal=False)),
                      Column('speed', Float(asdecimal=False)),
                      Column('first_time', INTEGER(11)),
                      Column('real_start_time', INTEGER(11)),
                      Column('goal_time', INTEGER(11)),
                      Column('last_time', INTEGER(11)),
                      Column('result', Enum('abs', 'dnf', 'lo', 'goal', 'mindist'), server_default=text("'lo'")),
                      Column('SS_time', INTEGER(11)),
                      Column('ES_time', INTEGER(11)),
                      Column('ES_rank', INTEGER(11)),
                      Column('turnpoints_made', INTEGER(11)),
                      Column('penalty', Float(asdecimal=False)),
                      Column('comment', Text),
                      Column('fixed_LC', Float(asdecimal=False)),
                      Column('ESS_altitude', INTEGER(11), server_default=text("'0'")),
                      Column('goal_altitude', INTEGER(11), server_default=text("'0'")),
                      Column('max_altitude', INTEGER(11), server_default=text("'0'")),
                      Column('last_altitude', INTEGER(11), server_default=text("'0'")),
                      Column('landing_altitude', INTEGER(11), server_default=text("'0'")),
                      Column('landing_time', INTEGER(11), server_default=text("'0'")),
                      Column('track_file', String(255)),
                      Column('g_record', TINYINT(4), server_default=text("'1'"))
                      )


class TaskStatsView(Base):
    __table__ = Table('TaskStatsView', metadata,

                      Column('task_id', INTEGER(11), primary_key=True),
                      Column('pilots_present', BIGINT(21)),
                      Column('tot_dist_flown', Float(asdecimal=False)),
                      Column('tot_dist_over_min', Float(asdecimal=False)),
                      Column('pilots_launched', BIGINT(21)),
                      Column('std_dev', Float(asdecimal=False)),
                      Column('pilots_landed', BIGINT(21)),
                      Column('pilots_goal', BIGINT(21)),
                      Column('pilots_ess', BIGINT(21)),
                      Column('max_distance', Float(asdecimal=False)),
                      Column('min_dept_time', BIGINT(11), server_default=text("'0'")),
                      Column('max_dept_time', BIGINT(11), server_default=text("'0'")),
                      Column('first_SS', BIGINT(11), server_default=text("'0'")),
                      Column('last_SS', BIGINT(11), server_default=text("'0'")),
                      Column('min_ess_time', BIGINT(11), server_default=text("'0'")),
                      Column('max_ess_time', BIGINT(11), server_default=text("'0'")),
                      Column('fastest_in_goal', BIGINT(12), server_default=text("'0'")),
                      Column('fastest', BIGINT(12), server_default=text("'0'")),
                      Column('max_time', BIGINT(11), server_default=text("'0'"))
                      )


class TaskView(Base):
    __table__ = Table('TaskView', metadata,

                      Column('task_id', INTEGER(11), primary_key=True),
                      Column('last_update', TIMESTAMP, nullable=False),
                      Column('comp_code', String(8)),
                      Column('comp_name', String(100)),
                      Column('comp_site', String(100)),
                      Column('time_offset', BIGINT(21)),
                      Column('comp_class', Enum('PG', 'HG', 'mixed'), server_default=text("'PG'")),
                      Column('comp_id', INTEGER(11)),
                      Column('date_from', Date),
                      Column('date_to', Date),
                      Column('cat_id', INTEGER(11)),
                      Column('sanction', Enum('League', 'PWC', 'FAI 2', 'none', 'FAI 1'),
                             server_default=text("'none'")),
                      Column('comp_type', Enum('RACE', 'Route', 'Team-RACE'), server_default=text("'RACE'")),
                      Column('restricted', Enum('open', 'registered'), server_default=text("'registered'")),
                      Column('date', Date),
                      Column('task_name', String(100)),
                      Column('task_num', TINYINT(4)),
                      Column('reg_id', INTEGER(11)),
                      Column('window_open_time', BIGINT(21)),
                      Column('task_deadline', BIGINT(21)),
                      Column('window_close_time', BIGINT(21)),
                      Column('check_launch', Enum('on', 'off'), server_default=text("'off'")),
                      Column('start_time', BIGINT(21)),
                      Column('SS_interval', BIGINT(13)),
                      Column('start_iteration', SMALLINT(6)),
                      Column('start_close_time', BIGINT(21)),
                      Column('stopped_time', BIGINT(21)),
                      Column('task_type', String(21)),
                      Column('distance', Float(asdecimal=False)),
                      Column('opt_dist', Float(asdecimal=False)),
                      Column('opt_dist_to_SS', Float(asdecimal=False)),
                      Column('opt_dist_to_ESS', Float(asdecimal=False)),
                      Column('SS_distance', Float(asdecimal=False)),
                      Column('formula_type', String(10)),
                      Column('formula_version', INTEGER(8)),
                      Column('formula_name', String(50)),
                      Column('nominal_goal', Float, server_default=text("'0.3'")),
                      Column('min_dist', Float(asdecimal=False), server_default=text("'0'")),
                      Column('nominal_dist', Float(asdecimal=False), server_default=text("'0'")),
                      Column('nominal_time', Float(asdecimal=False), server_default=text("'0'")),
                      Column('nominal_launch', Float, server_default=text("'0.96'")),
                      Column('formula_distance', String(10)),
                      Column('formula_departure', String(9)),
                      Column('formula_arrival', String(8)),
                      Column('formula_time', String(3)),
                      Column('lead_factor', Float),
                      Column('no_goal_penalty', Float(20, False), server_default=text("'0.000'")),
                      Column('glide_bonus', Float, server_default=text("'4'")),
                      Column('tolerance', Float(21, False)),
                      Column('min_tolerance', INTEGER(4)),
                      Column('airspace_check', TINYINT(1)),
                      Column('openair_file', String(40)),
                      Column('arr_alt_bonus', Float(asdecimal=False), server_default=text("'0'")),
                      Column('arr_min_height', INTEGER(11)),
                      Column('arr_max_height', INTEGER(11)),
                      Column('validity_min_time', BIGINT(13)),
                      Column('score_back_time', BIGINT(13), server_default=text("'0'")),
                      Column('max_JTG', SMALLINT(6)),
                      Column('JTG_penalty_per_sec', Float),
                      Column('scoring_altitude', Enum('GPS', 'QNH'), server_default=text("'GPS'")),
                      Column('comment', Text),
                      Column('locked', TINYINT(3), server_default=text("'0'")),
                      Column('launch_valid', BIGINT(11)),
                      Column('comp_path', String(40)),
                      Column('task_path', String(40))
                      )


class TaskWaypointView(Base):
    __table__ = Table('TaskWaypointView', metadata,

                      Column('id', INTEGER(11), primary_key=True),
                      Column('task_id', INTEGER(11)),
                      Column('n', INTEGER(11)),
                      Column('name', CHAR(6)),
                      Column('lat', Float),
                      Column('lon', Float),
                      Column('altitude', INTEGER(11)),
                      Column('description', String(80)),
                      Column('how', Enum('entry', 'exit'), server_default=text("'entry'")),
                      Column('radius', INTEGER(11)),
                      Column('shape', Enum('circle', 'semicircle', 'line'), server_default=text("'circle'")),
                      Column('type', Enum('waypoint', 'launch', 'speed', 'endspeed', 'goal'),
                             server_default=text("'waypoint'")),
                      Column('ssr_lat', Float(asdecimal=False)),
                      Column('ssr_lon', Float(asdecimal=False)),
                      Column('partial_distance', Float(asdecimal=False))
                      )


class TaskAirspaceCheckView(Base):
    __table__ = Table('TaskAirspaceCheckView', metadata,

                      Column('task_id', INTEGER(11), primary_key=True),
                      Column('airspace_check', TINYINT(1)),
                      Column('notification_distance', SMALLINT(4)),
                      Column('outer_limit', SMALLINT(4)),
                      Column('inner_limit', SMALLINT(4)),
                      Column('border_penalty', Float(asdecimal=False)),
                      Column('max_penalty', Float(asdecimal=False))
                      )


class TaskXContestWptView(Base):
    __table__ = Table('TaskXContestWptView', metadata,

                      Column('tasPk', INTEGER(11), primary_key=True),
                      Column('tasDate', Date),
                      Column('tasGoalAlt', Float(asdecimal=False)),
                      Column('xccSiteID', BIGINT(11)),
                      Column('xccToID', BIGINT(11))
                      )


class UserView(Base):
    __table__ = Table('UserView', metadata,

                      Column('usePk', BIGINT(20), primary_key=True),
                      Column('useName', String(250)),
                      Column('useLogin', String(60)),
                      Column('useEmail', String(100))
                      )


class TrackFileView(Base):
    __table__ = Table('TrackFileView', metadata,

                      Column('track_id', INTEGER(11), primary_key=True),
                      Column('task_id', INTEGER(11)),
                      Column('par_id', INTEGER(11)),
                      Column('filename', String(255)),
                      Column('g_record', TINYINT(4))
                      )


class TrackObjectView(Base):
    __table__ = Table('TrackObjectView', metadata,

                      Column('track_id', INTEGER(11), primary_key=True),
                      Column('par_id', INTEGER(11)),
                      Column('task_id', INTEGER(11)),
                      Column('civl_id', INTEGER(10)),
                      Column('glider', String(100)),
                      Column('glider_cert', String(20)),
                      Column('track_file', String(255)),
                      )


schema_version = Table(
    'schema_version', metadata,
    Column('svKey', INTEGER(11), nullable=False, server_default=text("'0'")),
    Column('svWhen', TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP")),
    Column('svExtra', String(256))
)


class tblAirspace(Base):
    __tablename__ = 'tblAirspace'

    airPk = Column(INTEGER(11), primary_key=True)
    airName = Column(String(32))
    airClass = Column(Enum('G', 'C', 'D', 'E', 'X', 'R', 'P', 'Q', 'W', 'GP', 'CTR'), server_default=text("'C'"))
    airBase = Column(INTEGER(11))
    airTops = Column(INTEGER(11))
    airShape = Column(Enum('circle', 'wedge', 'polygon'), server_default=text("'circle'"))
    airCentreWP = Column(INTEGER(11))
    airRadius = Column(Float)


class tblAirspaceRegion(Base):
    __tablename__ = 'tblAirspaceRegion'

    argPk = Column(INTEGER(11), primary_key=True)
    argRegion = Column(String(32), nullable=False)
    argLatDecimal = Column(Float(asdecimal=False), nullable=False)
    argLongDecimal = Column(Float(asdecimal=False), nullable=False)
    argSize = Column(Float, nullable=False)


class tblAirspaceWaypoint(Base):
    __tablename__ = 'tblAirspaceWaypoint'

    awpPk = Column(INTEGER(11), primary_key=True)
    airPk = Column(ForeignKey('tblAirspace.airPk', ondelete='CASCADE'), nullable=False, index=True)
    airOrder = Column(INTEGER(11), nullable=False)
    awpConnect = Column(Enum('line', 'arc+', 'arc-'), server_default=text("'line'"))
    awpLatDecimal = Column(Float(asdecimal=False), nullable=False)
    awpLongDecimal = Column(Float(asdecimal=False), nullable=False)
    awpAngleStart = Column(Float)
    awpAngleEnd = Column(Float)
    awpRadius = Column(Float)

    tblAirspace = relationship('tblAirspace')


class tblCertification(Base):
    __tablename__ = 'tblCertification'

    cerPk = Column(INTEGER(11), primary_key=True)
    cerName = Column(String(15), nullable=False)
    comClass = Column(Enum('PG', 'HG', 'mixed'), nullable=False, server_default=text("'PG'"))


class tblClasCertRank(Base):
    __tablename__ = 'tblClasCertRank'
    __table_args__ = (
        PrimaryKeyConstraint('claPk'),
    )

    claPk = Column(ForeignKey('tblClassification.claPk', ondelete='CASCADE'), index=True)
    cerPk = Column(ForeignKey('tblCertification.cerPk'), index=True)
    ranPk = Column(ForeignKey('tblRanking.ranPk'), nullable=False, index=True)

    tblClassification = relationship('tblClassification')
    tblCertification = relationship('tblCertification')
    tblRanking = relationship('tblRanking')


# tblClasCertRank = Table(
#     'tblClasCertRank', metadata,
#     Column('claPk', ForeignKey('tblClassification.claPk', ondelete='CASCADE'), nullable=False, index=True),
#     Column('cerPk', ForeignKey('tblCertification.cerPk'), index=True),
#     Column('ranPk', ForeignKey('tblRanking.ranPk'), nullable=False, index=True)
# )

# class tblClasCertRank(Base):
#     __tablename__ = 'tblClasCertRank'
#
#     claPk = Column(INTEGER(11), primary_key=True)
#     cerPk = Column(INTEGER(11), nullable=False)
#     ranPk = Column(INTEGER(11), nullable=False)

class tblClassification(Base):
    __tablename__ = 'tblClassification'

    claPk = Column(INTEGER(11), primary_key=True)
    claName = Column(String(60), nullable=False)
    comClass = Column(Enum('PG', 'HG', 'mixed'), nullable=False, server_default=text("'PG'"))
    claFem = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    claTeam = Column(TINYINT(1), nullable=False, server_default=text("'0'"))


class tblCompAuth(Base):
    __table__ = Table('tblCompAuth', metadata,

                      Column('usePk', INTEGER(11), primary_key=True),
                      Column('comPk', INTEGER(11)),
                      Column('useLevel', Enum('read', 'write', 'admin'), server_default=text("'read'"))
                      )


class tblCompetition(Base):
    __tablename__ = 'tblCompetition'
    __table_args__ = (
        Index('comPk', 'comPk', 'comName', unique=True),
    )

    comPk = Column(INTEGER(11), primary_key=True)
    comName = Column(String(100), nullable=False)
    comCode = Column(String(8))
    comLastUpdate = Column(TIMESTAMP, nullable=False,
                           server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    comLocation = Column(String(100), nullable=False)
    comDateFrom = Column(DateTime, nullable=False)
    comDateTo = Column(DateTime, nullable=False)
    comMeetDirName = Column(String(100))
    comContact = Column(String(100))
    claPk = Column(ForeignKey('tblClassification.claPk', ondelete='SET NULL'), index=True)
    comSanction = Column(Enum('League', 'PWC', 'FAI 2', 'none', 'FAI 1'), nullable=False, server_default=text("'none'"))
    comOpenAirFile = Column(String(40))
    comType = Column(Enum('RACE', 'Route', 'Team-RACE'), server_default=text("'RACE'"))
    comEntryRestrict = Column(Enum('open', 'registered'), server_default=text("'registered'"))
    comTimeOffset = Column(Float(asdecimal=False), server_default=text("'11'"))
    comTrackSource = Column(String(40))
    comClass = Column(Enum('PG', 'HG', 'mixed'), server_default=text("'PG'"))
    comStyleSheet = Column(String(128))
    comLocked = Column(INTEGER(11), server_default=text("'0'"))
    comExt = Column(INTEGER(2), nullable=False, server_default=text("'0'"))
    comExtUrl = Column(String(100))
    comPath = Column(String(40))

    tblClassification = relationship('tblClassification')
    tblLadder = relationship('tblLadder', secondary='tblLadderComp')


class tblCountryCode(Base):
    __tablename__ = 'tblCountryCode'

    natName = Column(String(52), nullable=False)
    natIso2 = Column(String(2), nullable=False)
    natIso3 = Column(String(3), nullable=False)
    natId = Column(INTEGER(11), primary_key=True)
    natIso = Column(String(13))
    natRegion = Column(String(8))
    natSubRegion = Column(String(25))
    natRegionId = Column(INTEGER(11))
    natSubRegionId = Column(INTEGER(11))


class tblExtPilot(Base):
    __tablename__ = 'tblExtPilot'

    pilPk = Column(INTEGER(11), primary_key=True)
    pilFirstName = Column(String(100), index=True)
    pilLastName = Column(String(100), index=True)
    pilEmail = Column(VARCHAR(100), nullable=False, server_default=text("''"))
    pilNat = Column(String(255))
    pilPhoneMobile = Column(String(255))
    pilSex = Column(VARCHAR(1), nullable=False, server_default=text("''"))
    pilGliderBrand = Column(String(255))
    pilGlider = Column(String(255))
    gliGliderCert = Column(Enum('A', 'B', 'C', 'D', 'CCC', 'floater', 'kingpost', 'open', 'rigid'))
    gliGliderClass = Column(VARCHAR(12))
    pilSponsor = Column(String(255))
    pilFAI = Column(String(255), index=True)
    pilCIVL = Column(String(255))
    pilLT24User = Column(String(255))
    pilATUser = Column(String(255))
    pilXcontestUser = Column(String(255))


class tblExtResult(Base):
    __tablename__ = 'tblExtResult'

    etrPk = Column(INTEGER(11), primary_key=True)
    tasPk = Column(INTEGER(11), index=True)
    parPk = Column(INTEGER(11), nullable=False)
    pilPk = Column(INTEGER(11))
    tarDistance = Column(Float(asdecimal=False))
    tarSpeed = Column(Float(asdecimal=False))
    tarStart = Column(INTEGER(11))
    tarGoal = Column(INTEGER(11))
    tarResultType = Column(Enum('abs', 'dnf', 'lo', 'goal', 'mindist'), server_default=text("'lo'"))
    tarSS = Column(INTEGER(11))
    tarES = Column(INTEGER(11))
    tarTurnpoints = Column(INTEGER(11))
    tarPenalty = Column(Float(asdecimal=False))
    tarComment = Column(Text)
    tarPlace = Column(INTEGER(11))
    tarSpeedScore = Column(Float(asdecimal=False))
    tarDistanceScore = Column(Float(asdecimal=False))
    tarArrivalScore = Column(Float(asdecimal=False))
    tarDepartureScore = Column(Float(asdecimal=False))
    tarScore = Column(Float(asdecimal=False))
    tarLeadingCoeff = Column(Float(asdecimal=False))
    tarFixedLC = Column(Float(asdecimal=False))
    tarESAltitude = Column(INTEGER(11), nullable=False, server_default=text("'0'"))
    tarMaxAltitude = Column(INTEGER(11), nullable=False, server_default=text("'0'"))
    tarLastAltitude = Column(INTEGER(11), server_default=text("'0'"))
    tarLastTime = Column(INTEGER(11))
    traGlider = Column(String(50))


class tblExtTask(Base):
    __tablename__ = 'tblExtTask'

    extPk = Column(INTEGER(11), primary_key=True)
    comPk = Column(INTEGER(11), nullable=False)
    comDateTo = Column(Date)
    tasName = Column(String(32))
    lcValue = Column(INTEGER(11), server_default=text("'450'"))
    tasQuality = Column(Float(asdecimal=False))
    tasTopScore = Column(INTEGER(11))
    extURL = Column(String(128))


class tblForComp(Base):
    __tablename__ = 'tblForComp'

    forPk = Column(ForeignKey('tblFormula.forPk', ondelete='SET NULL'), index=True)
    comPk = Column(INTEGER(11), primary_key=True)
    forLastUpdate = Column(TIMESTAMP, nullable=False,
                           server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    forClass = Column(String(10))
    forVersion = Column(INTEGER(8))
    forName = Column(String(20))
    extForName = Column(String(50))
    comOverallScore = Column(Enum('ftv', 'all', 'round'), nullable=False, server_default=text("'ftv'"))
    comOverallParam = Column(Float, nullable=False, server_default=text("'0.75'"))
    forNomGoal = Column(Float, nullable=False, server_default=text("'0.3'"))
    forMinDistance = Column(Float, nullable=False, server_default=text("'5'"))
    forNomDistance = Column(Float, nullable=False, server_default=text("'45'"))
    forNomTime = Column(Float, nullable=False, server_default=text("'90'"))
    forNomLaunch = Column(Float, nullable=False, server_default=text("'0.96'"))
    forDistance = Column(Enum('on', 'difficulty', 'off'), nullable=False, server_default=text("'on'"))
    forArrival = Column(Enum('position', 'time', 'off'), nullable=False, server_default=text("'off'"))
    forDeparture = Column(Enum('leadout', 'departure', 'off'), nullable=False, server_default=text("'leadout'"))
    forLeadFactor = Column(Float)
    forTime = Column(Enum('on', 'off'), nullable=False, server_default=text("'on'"))
    forNoGoalPenalty = Column(Float, nullable=False, server_default=text("'1'"))
    forGlideBonus = Column(Float, nullable=False, server_default=text("'4'"))
    forTolerance = Column(Float, nullable=False, server_default=text("'0.1'"))
    forMinTolerance = Column(INTEGER(4), nullable=False, server_default=text("'5'"))
    forHeightBonus = Column(Float, nullable=False, server_default=text("'0'"))
    forESSHeightLo = Column(INTEGER(11))
    forESSHeightUp = Column(INTEGER(11))
    forMinTime = Column(INTEGER(11))
    forScorebackTime = Column(INTEGER(11), nullable=False, server_default=text("'5'"))
    forMaxJTG = Column(SMALLINT, nullable=False, server_default=text("'0'"))
    forJTGPenPerSec = Column(Float)
    forAltitudeMode = Column(Enum('GPS', 'QNH'), nullable=False, server_default=text("'GPS'"))
    comTeamSize = Column(INTEGER(4), nullable=False, server_default=text("'0'"))
    comTeamScoring = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    comCountryScoring = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    comTeamOver = Column(INTEGER(2))

    tblFormula = relationship('tblFormula')


class tblFormula(Base):
    __tablename__ = 'tblFormula'

    forPk = Column(INTEGER(11), primary_key=True)
    forClass = Column(Enum('gap', 'pwc', 'RTG'), nullable=False, server_default=text("'pwc'"))
    forVersion = Column(String(32))
    forComClass = Column(Enum('PG', 'HG', 'mixed'), nullable=False, server_default=text("'PG'"))
    forName = Column(String(32), nullable=False)
    forArrival = Column(Enum('off', 'position', 'time'), server_default=text("'none'"))
    forDeparture = Column(Enum('off', 'departure', 'leadout'), server_default=text("'leadout'"))
    forLinearDist = Column(Float(asdecimal=False), server_default=text("'1'"))
    forDiffDist = Column(Float(asdecimal=False), server_default=text("'3'"))
    forDistMeasure = Column(Enum('average', 'median'), server_default=text("'average'"))
    forDiffRamp = Column(Enum('fixed', 'flexible'), server_default=text("'fixed'"))
    forDiffCalc = Column(Enum('all', 'lo'), server_default=text("'all'"))
    forGoalSSpenalty = Column(Float(asdecimal=False), server_default=text("'1'"))
    forStoppedGlideBonus = Column(Float(asdecimal=False), server_default=text("'4'"))
    forMargin = Column(Float(asdecimal=False), server_default=text("'0.5'"))
    forStoppedElapsedCalc = Column(Enum('atstopped', 'shortesttime'), server_default=text("'shortesttime'"))
    forHeightArrBonus = Column(Float(asdecimal=False), server_default=text("'0'"))
    forHeightArrLower = Column(INTEGER(11), server_default=text("'200'"))
    forHeightArrUpper = Column(INTEGER(11), server_default=text("'3000'"))
    forWeightStart = Column(Float(asdecimal=False), server_default=text("'0.125'"))
    forWeightArrival = Column(Float(asdecimal=False), server_default=text("'0.175'"))
    forWeightSpeed = Column(Float(asdecimal=False), server_default=text("'0.7'"))


class tblGlider(Base):
    __tablename__ = 'tblGlider'

    gliPk = Column(INTEGER(11), primary_key=True)
    gliName = Column(String(32))
    gliManufacturer = Column(String(32))
    gliClass = Column(Enum('PG', 'HG'), server_default=text("'PG'"))
    gliDHV = Column(Enum('1', '1/2', '2', '2/3', 'competition', 'floater', 'kingpost', 'open', 'rigid'),
                    server_default=text("'competition'"))


class tblLadder(Base):
    __tablename__ = 'tblLadder'

    ladPk = Column(INTEGER(11), primary_key=True)
    ladName = Column(String(100), nullable=False)
    ladComClass = Column(Enum('PG', 'HG'), nullable=False, server_default=text("'PG'"))
    ladNationCode = Column(INTEGER(11), server_default=text("'380'"))
    ladStart = Column(Date)
    ladEnd = Column(Date)
    ladIncExternal = Column(INTEGER(11), server_default=text("'0'"))
    ladImageM = Column(String(128))
    ladImageF = Column(String(128))


tblLadderComp = Table(
    'tblLadderComp', metadata,
    Column('ladPk', ForeignKey('tblLadder.ladPk', ondelete='CASCADE'), index=True),
    Column('comPk', ForeignKey('tblCompetition.comPk', ondelete='CASCADE'), index=True)
)

tblLadderSeason = Table(
    'tblLadderSeason', metadata,
    Column('ladPk', ForeignKey('tblLadder.ladPk'), nullable=False, index=True),
    Column('seasonYear', INTEGER(11), nullable=False, index=True),
    Column('ladActive', TINYINT(1), server_default=text("'1'")),
    Column('claPk', ForeignKey('tblClassification.claPk'), nullable=False, index=True),
    Column('ladOverallScore', Enum('all', 'ftv', 'round'), nullable=False, server_default=text("'ftv'")),
    Column('ladOverallParam', Float(asdecimal=False), nullable=False)
)


class tblLaunchSite(Base):
    __tablename__ = 'tblLaunchSite'

    lauPk = Column(INTEGER(11), primary_key=True)
    lauLaunch = Column(String(32), nullable=False)
    lauRegion = Column(String(32), nullable=False)
    lauLatDecimal = Column(Float(asdecimal=False), nullable=False)
    lauLongDecimal = Column(Float(asdecimal=False), nullable=False)
    lauAltitude = Column(Float(asdecimal=False), nullable=False)


class tblRanking(Base):
    __tablename__ = 'tblRanking'

    ranPk = Column(INTEGER(11), primary_key=True)
    ranName = Column(String(40), nullable=False)
    comClass = Column(Enum('PG', 'HG', 'mixed'), nullable=False, server_default=text("'PG'"))


class tblRegion(Base):
    __tablename__ = 'tblRegion'

    regPk = Column(INTEGER(11), primary_key=True)
    regCentre = Column(INTEGER(11))
    regRadius = Column(Float(asdecimal=False))
    regDescription = Column(String(64), nullable=False)
    regWptFileName = Column(String(50), nullable=False)
    regOpenAirFile = Column(String(50), nullable=False)


tblRegionAuth = Table(
    'tblRegionAuth', metadata,
    Column('usePk', INTEGER(11)),
    Column('comPk', INTEGER(11)),
    Column('useLevel', Enum('read', 'write', 'admin'), server_default=text("'read'"))
)


class tblRegionWaypoint(Base):
    __tablename__ = 'tblRegionWaypoint'

    rwpPk = Column(INTEGER(11), primary_key=True)
    regPk = Column(ForeignKey('tblRegion.regPk'), index=True)
    rwpName = Column(String(12), nullable=False)
    rwpLatDecimal = Column(Float(asdecimal=False), nullable=False)
    rwpLongDecimal = Column(Float(asdecimal=False), nullable=False)
    rwpAltitude = Column(Float(asdecimal=False), nullable=False)
    rwpDescription = Column(String(64))
    rwpOld = Column(TINYINT(4), nullable=False, server_default=text("'0'"))
    xccSiteID = Column(INTEGER(11))
    xccToID = Column(INTEGER(11))

    tblRegion = relationship('tblRegion')


tblRegionXCSites = Table(
    'tblRegionXCSites', metadata,
    Column('regPk', ForeignKey('tblRegion.regPk', ondelete='CASCADE'), nullable=False, index=True),
    Column('xccSiteID', INTEGER(11), nullable=False, index=True)
)


class tblParticipant(Base):
    __tablename__ = 'tblParticipant'
    __table_args__ = (
        Index('parPk', 'pilPk', 'comPk'),
    )

    parPk = Column(INTEGER(11), primary_key=True)
    comPk = Column(INTEGER(11))
    CIVLID = Column(INTEGER(10))
    pilPk = Column(INTEGER(11))
    parID = Column(INTEGER(4))
    parName = Column(String(50))
    parBirthdate = Column(CHAR(10))
    parSex = Column(Enum('M', 'F'), nullable=False, server_default=text("'M'"))
    parNat = Column(CHAR(10))
    parGlider = Column(String(100))
    parCert = Column(String(20))
    parClass = Column(String(50))
    parSponsor = Column(String(100))
    parValidFAI = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    parFAI = Column(String(20))
    parXC = Column(String(20))
    parLiveID = Column(String(10))
    parTeam = Column(String(100))
    parNatTeam = Column(TINYINT(4), nullable=False, server_default=text("'1'"))
    parStatus = Column(Enum('confirmed', 'wild card', 'waiting list', 'cancelled', 'waiting for payment'))
    parRanking = Column(INTEGER(11))
    parPaid = Column(INTEGER(11), server_default=text("'0'"))
    parHours = Column(INTEGER(11), server_default=text("'200'"))


class tblResultFile(Base):
    __tablename__ = 'tblResultFile'

    refPk = Column(INTEGER(11), primary_key=True)
    comPk = Column(INTEGER(11), nullable=False)
    tasPk = Column(INTEGER(11))
    refTimestamp = Column(INTEGER(11), nullable=False)
    refJSON = Column(MEDIUMTEXT)
    refStatus = Column(VARCHAR(255))
    refVisible = Column(TINYINT(1), nullable=False, server_default=text("'0'"))


class tblTask(Base):
    __tablename__ = 'tblTask'

    tasPk = Column(INTEGER(11), primary_key=True)
    comPk = Column(ForeignKey('tblCompetition.comPk'), index=True)
    tasLastUpdate = Column(TIMESTAMP, nullable=False,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    tasNum = Column(TINYINT(4), nullable=False)
    tasName = Column(String(100))
    tasDate = Column(Date, nullable=False)
    regPk = Column(ForeignKey('tblRegion.regPk'), index=True)
    tasTaskStart = Column(DateTime)
    tasFinishTime = Column(DateTime)
    tasLaunchClose = Column(DateTime)
    tasCheckLaunch = Column(Enum('on', 'off'), server_default=text("'off'"))
    tasStartTime = Column(DateTime)
    tasSSInterval = Column(INTEGER(11), server_default=text("'0'"))
    tasStartIteration = Column(TINYINT)
    tasStartCloseTime = Column(DateTime)
    tasStoppedTime = Column(DateTime)
    tasResultsType = Column(String(20))
    tasTaskType = Column(Enum('race', 'elapsed time', 'free distance', 'distance with bearing'),
                         server_default=text("'race'"))
    tasDistance = Column(Float)
    tasShortRouteDistance = Column(Float)
    tasStartSSDistance = Column(Float)
    tasEndSSDistance = Column(Float)
    tasSSDistance = Column(Float)
    tasLaunchValid = Column(INTEGER(11), server_default=text("'1'"))
    tasDistOverride = Column(Enum('on', 'difficulty', 'off'))
    tasDepOverride = Column(Enum('leadout', 'departure', 'off'))
    tasArrOverride = Column(Enum('position', 'time', 'off'))
    tasTimeOverride = Column(Enum('on', 'off'))
    tasHeightBonusOverride = Column(Float)
    tasJTGOverride = Column(TINYINT(1))
    tasNoGoalOverride = Column(TINYINT(1))
    tasMarginOverride = Column(Float)
    tasAirspaceCheckOverride = Column(TINYINT(1))
    tasOpenAirOverride = Column(String(40))
    tasComment = Column(Text)
    tasLocked = Column(TINYINT(3), nullable=False, server_default=text("'0'"))
    tasPath = Column(String(40))

    tblCompetition = relationship('tblCompetition')
    tblRegion = relationship('tblRegion')


class tblTaskAirspace(Base):
    __tablename__ = 'tblTaskAirspace'

    taPk = Column(INTEGER(11), primary_key=True)
    tasPk = Column(ForeignKey('tblTask.tasPk', ondelete='CASCADE'), nullable=False, index=True)
    airPk = Column(ForeignKey('tblAirspace.airPk', ondelete='CASCADE'), nullable=False, index=True)

    tblAirspace = relationship('tblAirspace')
    tblTask = relationship('tblTask')


class tblTaskResult(Base):
    __tablename__ = 'tblTaskResult'
    __table_args__ = (
        Index('tarPk', 'tarPk', 'tasPk', 'parPk', unique=True),
    )

    tarPk = Column(INTEGER(11), primary_key=True)
    tasPk = Column(ForeignKey('tblTask.tasPk'), index=True)
    parPk = Column(INTEGER(11), index=True)
    tarLastUpdate = Column(TIMESTAMP, nullable=False,
                           server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    traFile = Column(String(255))
    traGRecordOk = Column(TINYINT(4), server_default=text("'1'"))
    tarDistance = Column(Float(asdecimal=False))
    tarLaunch = Column(INTEGER(11))
    tarStart = Column(INTEGER(11))
    tarSS = Column(INTEGER(11))
    tarES = Column(INTEGER(11))
    tarGoal = Column(INTEGER(11))
    tarLastTime = Column(INTEGER(11))
    tarSpeed = Column(Float(asdecimal=False))
    tarTurnpoints = Column(INTEGER(11))
    tarESAltitude = Column(INTEGER(11), nullable=False, server_default=text("'0'"))
    tarGoalAltitude = Column(INTEGER(11), nullable=False, server_default=text("'0'"))
    tarMaxAltitude = Column(INTEGER(11), nullable=False, server_default=text("'0'"))
    tarLastAltitude = Column(INTEGER(11), server_default=text("'0'"))
    tarLandingTime = Column(INTEGER(11), nullable=False, server_default=text("'0'"))
    tarLandingAltitude = Column(INTEGER(11), nullable=False, server_default=text("'0'"))
    tarResultType = Column(Enum('abs', 'dnf', 'lo', 'goal', 'mindist'), server_default=text("'lo'"))
    tarPenalty = Column(Float(asdecimal=False))
    tarComment = Column(Text)
    tarPlace = Column(INTEGER(11))
    tarDistanceScore = Column(Float(asdecimal=False))
    tarSpeedScore = Column(Float(asdecimal=False))
    tarArrivalScore = Column(Float(asdecimal=False))
    tarDepartureScore = Column(Float(asdecimal=False))
    tarScore = Column(Float(asdecimal=False))
    tarLeadingCoeff = Column(Float(asdecimal=False))
    tarFixedLC = Column(Float(asdecimal=False))

    tblTask = relationship('tblTask')


class tblTaskWaypoint(Base):
    __tablename__ = 'tblTaskWaypoint'

    tawPk = Column(INTEGER(11), primary_key=True)
    tasPk = Column(ForeignKey('tblTask.tasPk', ondelete='SET NULL'), index=True)
    rwpPk = Column(ForeignKey('tblRegionWaypoint.rwpPk', ondelete='SET NULL'), index=True)
    tawNumber = Column(INTEGER(11), nullable=False)
    tawName = Column(CHAR(6), nullable=False)
    tawLat = Column(Float, nullable=False)
    tawLon = Column(Float, nullable=False)
    tawAlt = Column(INTEGER(11), nullable=False, server_default=text("'0'"))
    tawDesc = Column(String(80))
    tawTime = Column(INTEGER(11))
    tawType = Column(Enum('waypoint', 'launch', 'speed', 'endspeed', 'goal'), index=True,
                     server_default=text("'waypoint'"))
    tawHow = Column(Enum('entry', 'exit'), server_default=text("'entry'"))
    tawShape = Column(Enum('circle', 'semicircle', 'line'), server_default=text("'circle'"))
    tawAngle = Column(INTEGER(11))
    tawRadius = Column(INTEGER(11))
    ssrLatDecimal = Column(Float(asdecimal=False))
    ssrLongDecimal = Column(Float(asdecimal=False))
    ssrCumulativeDist = Column(Float(asdecimal=False))

    tblRegionWaypoint = relationship('tblRegionWaypoint')
    tblTask = relationship('tblTask')


class tblTeam(Base):
    __tablename__ = 'tblTeam'

    teaPk = Column(INTEGER(11), primary_key=True)
    comPk = Column(INTEGER(11), index=True)
    teaName = Column(String(64))
    teaScoring = Column(INTEGER(11))


class tblTeamPilot(Base):
    __tablename__ = 'tblTeamPilot'
    __table_args__ = (
        Index('indTeamPilot', 'teaPk', 'parPk'),
    )

    tepPk = Column(INTEGER(11), primary_key=True)
    teaPk = Column(INTEGER(11))
    parPk = Column(ForeignKey('tblParticipant.parPk'), nullable=False, index=True)
    tepModifier = Column(Float)

    tblParticipant = relationship('tblParticipant')


tblUserSession = Table(
    'tblUserSession', metadata,
    Column('usePk', INTEGER(11), nullable=False),
    Column('useSession', String(128)),
    Column('useIP', String(32)),
    Column('useSessTime', TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP")),
    Column('useLastTime', TIMESTAMP, nullable=False, server_default=text("'0000-00-00 00:00:00'"))
)


class tblXContestCode(Base):
    __tablename__ = 'tblXContestCodes'

    xccSiteID = Column(INTEGER(11))
    xccSiteName = Column(String(40))
    xccToID = Column(INTEGER(11), primary_key=True)
    xccToName = Column(String(40), nullable=False)
    xccAlt = Column(INTEGER(11))
    xccISO = Column(String(2), nullable=False)
    xccCountryName = Column(String(42))
