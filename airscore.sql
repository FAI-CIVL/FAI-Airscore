
SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

-- --------------------------------------------------------

--
-- Stand-in structure for view `CompObjectView`
-- (See below for the actual view)
--
CREATE TABLE `CompObjectView` (
`comp_id` int(11)
,`comp_name` varchar(100)
,`comp_site` varchar(100)
,`date_from` date
,`date_to` date
,`MD_name` varchar(100)
,`contact` varchar(100)
,`cat_id` int(11)
,`sanction` varchar(20)
,`comp_type` enum('RACE','Route','Team-RACE')
,`comp_code` varchar(10)
,`restricted` tinyint(1)
,`time_offset` mediumint(9)
,`comp_class` enum('PG','HG','mixed')
,`openair_file` varchar(40)
,`stylesheet` varchar(128)
,`locked` tinyint(1)
,`comp_path` varchar(40)
,`external` int(2)
,`website` varchar(100)
,`airspace_check` tinyint(1)
,`check_launch` enum('on','off')
,`igc_config_file` varchar(80)
,`self_register` tinyint(1)
,`check_g_record` tinyint(1)
,`formula_type` varchar(10)
,`formula_version` int(8)
,`formula_name` varchar(50)
,`overall_validity` enum('ftv','all','round')
,`validity_param` float(4,3)
,`validity_ref` enum('day_quality','max_score')
,`nominal_goal` float(3,2)
,`min_dist` mediumint(9)
,`nominal_dist` mediumint(9)
,`nominal_time` smallint(6)
,`nominal_launch` float(3,2)
,`formula_distance` enum('on','difficulty','off')
,`formula_arrival` enum('position','time','off')
,`formula_departure` enum('leadout','departure','off')
,`lead_factor` float(4,2)
,`formula_time` enum('on','off')
,`no_goal_penalty` float(4,3)
,`glide_bonus` float(4,2)
,`tolerance` float(6,5)
,`min_tolerance` int(4)
,`arr_alt_bonus` float
,`arr_min_height` smallint(6)
,`arr_max_height` smallint(6)
,`validity_min_time` smallint(6)
,`score_back_time` smallint(6)
,`max_JTG` smallint(6)
,`JTG_penalty_per_sec` float(4,2)
,`scoring_altitude` enum('GPS','QNH')
,`task_result_decimal` int(2)
,`comp_result_decimal` int(2)
,`team_scoring` tinyint(1)
,`team_size` int(4)
,`max_team_size` int(4)
,`country_scoring` tinyint(1)
,`country_size` int(4)
,`max_country_size` int(4)
,`team_over` int(2)
);

-- --------------------------------------------------------

--
-- Stand-in structure for view `FlightResultView`
-- (See below for the actual view)
--
CREATE TABLE `FlightResultView` (
`track_id` int(11)
,`par_id` int(11)
,`task_id` int(11)
,`comp_id` int(11)
,`civl_id` int(10)
,`fai_id` varchar(20)
,`pil_id` int(11)
,`ID` int(4)
,`name` varchar(50)
,`nat` char(10)
,`sex` enum('M','F')
,`glider` varchar(100)
,`glider_cert` varchar(20)
,`sponsor` varchar(100)
,`team` varchar(100)
,`nat_team` tinyint(4)
,`live_id` varchar(10)
,`distance_flown` double
,`best_distance_time` mediumint(9)
,`stopped_distance` float
,`stopped_altitude` smallint(6)
,`total_distance` float
,`speed` double
,`first_time` mediumint(9)
,`real_start_time` mediumint(9)
,`goal_time` mediumint(9)
,`last_time` mediumint(9)
,`result_type` enum('abs','dnf','lo','goal','mindist','nyp')
,`SSS_time` mediumint(9)
,`ESS_time` mediumint(9)
,`waypoints_made` tinyint(4)
,`penalty` double
,`comment` text
,`time_score` double
,`distance_score` double
,`arrival_score` double
,`departure_score` double
,`score` double
,`lead_coeff` double
,`fixed_LC` double
,`ESS_altitude` smallint(6)
,`goal_altitude` smallint(6)
,`max_altitude` smallint(6)
,`last_altitude` smallint(6)
,`landing_altitude` smallint(6)
,`landing_time` mediumint(9)
,`track_file` varchar(255)
,`g_record` tinyint(4)
);

-- --------------------------------------------------------

--
-- Table structure for table `Pilots`
--

CREATE TABLE `Pilots` (
  `pil_id` bigint(20) UNSIGNED NOT NULL,
  `login` varchar(60) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci NOT NULL DEFAULT '',
  `pwd` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci NOT NULL DEFAULT '',
  `email` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci NOT NULL DEFAULT '',
  `first_name` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci,
  `last_name` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci,
  `nat` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci,
  `phone` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci,
  `sex` varchar(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `glider_brand` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci,
  `glider` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci,
  `glider_cert` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci,
  `glider_class` varchar(12) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `sponsor` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci,
  `fai_id` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci,
  `civl_id` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci,
  `livetrack24_id` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci,
  `airtribune_id` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci,
  `xcontest_id` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci,
  `telegram_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Stand-in structure for view `RegionWaypointView`
-- (See below for the actual view)
--
CREATE TABLE `RegionWaypointView` (
`rwp_id` int(11)
,`region_id` int(11)
,`name` varchar(12)
,`lat` float
,`lon` float
,`altitude` smallint(6)
,`description` varchar(64)
);

-- --------------------------------------------------------

--
-- Table structure for table `schema_version`
--

CREATE TABLE `schema_version` (
  `svKey` int(11) NOT NULL DEFAULT '0',
  `svWhen` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `svExtra` varchar(256) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Stand-in structure for view `TaskAirspaceCheckView`
-- (See below for the actual view)
--
CREATE TABLE `TaskAirspaceCheckView` (
`task_id` int(11)
,`airspace_check` tinyint(1)
,`notification_distance` smallint(4)
,`function` enum('linear','non-linear')
,`h_outer_limit` smallint(4)
,`h_inner_limit` smallint(4)
,`h_boundary` smallint(4)
,`h_boundary_penalty` float(3,2)
,`h_max_penalty` float(3,2)
,`v_outer_limit` smallint(4)
,`v_inner_limit` smallint(4)
,`v_boundary` smallint(4)
,`v_boundary_penalty` float(3,2)
,`v_max_penalty` float(3,2)
);

-- --------------------------------------------------------

--
-- Stand-in structure for view `TaskFormulaView`
-- (See below for the actual view)
--
CREATE TABLE `TaskFormulaView` (
`comp_id` int(11)
,`task_id` int(11)
,`formula_type` varchar(10)
,`formula_version` int(8)
,`formula_name` varchar(50)
,`overall_validity` enum('ftv','all','round')
,`validity_param` float(4,3)
,`validity_ref` enum('day_quality','max_score')
,`nominal_goal` float(3,2)
,`min_dist` mediumint(9)
,`nominal_dist` mediumint(9)
,`nominal_time` smallint(6)
,`nominal_launch` float(3,2)
,`formula_distance` enum('on','difficulty','off')
,`formula_departure` enum('leadout','departure','off')
,`formula_arrival` enum('position','time','off')
,`formula_time` enum('on','off')
,`lead_factor` float(4,2)
,`no_goal_penalty` float(4,3)
,`glide_bonus` float(4,2)
,`tolerance` float(6,5)
,`min_tolerance` int(4)
,`arr_alt_bonus` float
,`arr_min_height` smallint(6)
,`arr_max_height` smallint(6)
,`validity_min_time` smallint(6)
,`score_back_time` smallint(6)
,`max_JTG` smallint(6)
,`JTG_penalty_per_sec` float(4,2)
,`scoring_altitude` enum('GPS','QNH')
,`team_scoring` tinyint(1)
,`team_size` int(4)
,`max_team_size` int(4)
,`country_scoring` tinyint(1)
,`country_size` int(4)
,`max_country_size` int(4)
);

-- --------------------------------------------------------

--
-- Stand-in structure for view `TaskObjectView`
-- (See below for the actual view)
--
CREATE TABLE `TaskObjectView` (
`task_id` int(11)
,`comp_code` varchar(10)
,`comp_name` varchar(100)
,`comp_site` varchar(100)
,`time_offset` mediumint(9)
,`comp_class` enum('PG','HG','mixed')
,`comp_id` int(11)
,`date` date
,`task_name` varchar(100)
,`task_num` tinyint(4)
,`reg_id` int(11)
,`region_name` varchar(64)
,`window_open_time` mediumint(9)
,`task_deadline` mediumint(9)
,`window_close_time` mediumint(9)
,`check_launch` enum('on','off')
,`start_time` mediumint(9)
,`SS_interval` smallint(6)
,`start_iteration` tinyint(4)
,`start_close_time` mediumint(9)
,`stopped_time` mediumint(9)
,`task_type` varchar(21)
,`distance` float
,`opt_dist` float
,`opt_dist_to_SS` float
,`opt_dist_to_ESS` float
,`SS_distance` float
,`QNH` float(7,3)
,`comment` text
,`locked` tinyint(3)
,`airspace_check` tinyint(1)
,`openair_file` varchar(40)
,`cancelled` tinyint(1)
,`track_source` varchar(40)
,`task_path` varchar(40)
,`comp_path` varchar(40)
,`igc_config_file` varchar(80)
);

-- --------------------------------------------------------

--
-- Table structure for table `tblCertification`
--

CREATE TABLE `tblCertification` (
  `cert_id` int(11) NOT NULL,
  `cert_name` varchar(15) NOT NULL,
  `comp_class` enum('PG','HG','mixed') NOT NULL DEFAULT 'PG'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tblClasCertRank`
--

CREATE TABLE `tblClasCertRank` (
  `cat_id` int(11) NOT NULL,
  `cert_id` int(11) DEFAULT NULL,
  `rank_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tblClassification`
--

CREATE TABLE `tblClassification` (
  `cat_id` int(11) NOT NULL,
  `cat_name` varchar(60) NOT NULL,
  `comp_class` enum('PG','HG','mixed') NOT NULL DEFAULT 'PG',
  `female` tinyint(1) NOT NULL DEFAULT '1',
  `team` tinyint(1) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tblCompAirspaceCheck`
--

CREATE TABLE `tblCompAirspaceCheck` (
  `comp_id` int(11) NOT NULL,
  `notification_distance` smallint(4) NOT NULL DEFAULT '100',
  `function` enum('linear','non-linear') NOT NULL DEFAULT 'linear',
  `h_outer_limit` smallint(4) NOT NULL DEFAULT '70',
  `h_boundary` smallint(4) NOT NULL DEFAULT '0',
  `h_boundary_penalty` float(3,2) NOT NULL DEFAULT '0.10',
  `h_inner_limit` smallint(4) NOT NULL DEFAULT '-30',
  `h_max_penalty` float(3,2) NOT NULL DEFAULT '1.00',
  `v_outer_limit` smallint(4) NOT NULL DEFAULT '70',
  `v_boundary` smallint(4) NOT NULL DEFAULT '0',
  `v_boundary_penalty` float(3,2) NOT NULL DEFAULT '0.10',
  `v_inner_limit` smallint(4) NOT NULL DEFAULT '30',
  `v_max_penalty` float(3,2) NOT NULL DEFAULT '1.00'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tblCompAuth`
--

CREATE TABLE `tblCompAuth` (
  `user_id` int(11) NOT NULL,
  `comp_id` int(11) NOT NULL,
  `user_auth` enum('read','write','admin','owner') NOT NULL DEFAULT 'read'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tblCompetition`
--

CREATE TABLE `tblCompetition` (
  `comp_id` int(11) NOT NULL,
  `comp_name` varchar(100) NOT NULL,
  `comp_code` varchar(10) DEFAULT NULL,
  `comp_class` enum('PG','HG','mixed') DEFAULT 'PG',
  `comp_last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `comp_site` varchar(100) NOT NULL,
  `date_from` date NOT NULL,
  `date_to` date NOT NULL,
  `time_offset` mediumint(9) NOT NULL DEFAULT '0',
  `MD_name` varchar(100) DEFAULT NULL,
  `contact` varchar(100) DEFAULT NULL,
  `cat_id` int(11) DEFAULT NULL,
  `sanction` varchar(20) NOT NULL DEFAULT 'none',
  `openair_file` varchar(40) DEFAULT NULL,
  `comp_type` enum('RACE','Route','Team-RACE') DEFAULT 'RACE',
  `restricted` tinyint(1) NOT NULL DEFAULT '1',
  `track_source` varchar(40) DEFAULT NULL,
  `stylesheet` varchar(128) DEFAULT NULL,
  `locked` tinyint(1) DEFAULT '0',
  `external` int(2) NOT NULL DEFAULT '0',
  `website` varchar(100) DEFAULT NULL,
  `comp_path` varchar(40) DEFAULT NULL,
  `igc_config_file` varchar(80) DEFAULT NULL,
  `airspace_check` tinyint(1) DEFAULT NULL,
  `check_launch` enum('on','off') NOT NULL DEFAULT 'off',
  `self_register` tinyint(1) NOT NULL DEFAULT '0',
  `check_g_record` tinyint(1) DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tblCountryCode`
--

CREATE TABLE `tblCountryCode` (
  `natName` varchar(52) NOT NULL,
  `natIso2` varchar(2) NOT NULL,
  `natIso3` varchar(3) NOT NULL,
  `natId` int(11) NOT NULL,
  `natIso` varchar(13) DEFAULT NULL,
  `natRegion` varchar(8) DEFAULT NULL,
  `natSubRegion` varchar(25) DEFAULT NULL,
  `natRegionId` int(11) DEFAULT NULL,
  `natSubRegionId` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tblForComp`
--

CREATE TABLE `tblForComp` (
  `forPk` int(11) DEFAULT NULL,
  `comp_id` int(11) NOT NULL,
  `formula_last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `formula_type` varchar(10) DEFAULT NULL,
  `formula_version` int(8) DEFAULT NULL,
  `formula_name` varchar(20) DEFAULT NULL,
  `external_name` varchar(50) DEFAULT NULL,
  `overall_validity` enum('ftv','all','round') NOT NULL DEFAULT 'ftv',
  `validity_param` float(4,3) NOT NULL DEFAULT '0.750',
  `validity_ref` enum('day_quality','max_score') DEFAULT 'day_quality',
  `nominal_goal` float(3,2) NOT NULL DEFAULT '0.30',
  `min_dist` mediumint(9) NOT NULL DEFAULT '5000',
  `nominal_dist` mediumint(9) NOT NULL DEFAULT '45000',
  `nominal_time` smallint(6) NOT NULL DEFAULT '5400',
  `nominal_launch` float(3,2) NOT NULL DEFAULT '0.96',
  `formula_distance` enum('on','difficulty','off') NOT NULL DEFAULT 'on',
  `formula_arrival` enum('position','time','off') NOT NULL DEFAULT 'off',
  `formula_departure` enum('leadout','departure','off') NOT NULL DEFAULT 'leadout',
  `lead_factor` float(4,2) DEFAULT NULL,
  `formula_time` enum('on','off') NOT NULL DEFAULT 'on',
  `no_goal_penalty` float(4,3) NOT NULL DEFAULT '1.000',
  `glide_bonus` float(4,2) NOT NULL DEFAULT '4.00',
  `tolerance` float(6,5) NOT NULL DEFAULT '0.10000',
  `min_tolerance` int(4) NOT NULL DEFAULT '5',
  `arr_alt_bonus` float NOT NULL DEFAULT '0',
  `arr_min_height` smallint(6) DEFAULT NULL,
  `arr_max_height` smallint(6) DEFAULT NULL,
  `validity_min_time` smallint(6) DEFAULT NULL,
  `score_back_time` smallint(6) NOT NULL DEFAULT '300',
  `max_JTG` smallint(6) NOT NULL DEFAULT '0',
  `JTG_penalty_per_sec` float(4,2) DEFAULT NULL,
  `scoring_altitude` enum('GPS','QNH') NOT NULL DEFAULT 'GPS',
  `task_result_decimal` int(2) DEFAULT '0',
  `comp_result_decimal` int(2) DEFAULT '0',
  `team_scoring` tinyint(1) NOT NULL DEFAULT '0',
  `team_size` int(4) DEFAULT NULL,
  `max_team_size` int(4) DEFAULT NULL,
  `country_scoring` tinyint(1) NOT NULL DEFAULT '0',
  `country_size` int(4) DEFAULT NULL,
  `max_country_size` int(4) DEFAULT NULL,
  `team_over` int(2) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tblLadder`
--

CREATE TABLE `tblLadder` (
  `ladder_id` int(11) NOT NULL,
  `ladder_name` varchar(100) NOT NULL,
  `ladder_class` enum('PG','HG') NOT NULL DEFAULT 'PG',
  `nation_code` int(11) DEFAULT '380',
  `date_from` date DEFAULT NULL,
  `date_to` date DEFAULT NULL,
  `external` tinyint(1) DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tblLadderComp`
--

CREATE TABLE `tblLadderComp` (
  `ladder_id` int(11) DEFAULT NULL,
  `comp_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tblLadderSeason`
--

CREATE TABLE `tblLadderSeason` (
  `ladder_id` int(11) NOT NULL,
  `season` int(6) NOT NULL,
  `active` tinyint(1) DEFAULT '1',
  `cat_id` int(11) NOT NULL,
  `overall_validity` enum('all','ftv','round') NOT NULL DEFAULT 'ftv',
  `validity_param` float NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tblNotification`
--

CREATE TABLE `tblNotification` (
  `not_id` int(11) NOT NULL,
  `track_id` int(11) NOT NULL,
  `notification_type` enum('admin','track','jtg','airspace') NOT NULL DEFAULT 'admin',
  `flat_penalty` float(8,4) NOT NULL DEFAULT '0.0000',
  `percentage_penalty` float(5,4) NOT NULL DEFAULT '0.0000',
  `comment` varchar(80) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tblParticipant`
--

CREATE TABLE `tblParticipant` (
  `par_id` int(11) NOT NULL,
  `comp_id` int(11) DEFAULT NULL,
  `civl_id` int(10) DEFAULT NULL,
  `pil_id` int(11) DEFAULT NULL,
  `ID` int(4) DEFAULT NULL,
  `name` varchar(50) DEFAULT NULL,
  `birthdate` date DEFAULT NULL,
  `sex` enum('M','F') NOT NULL DEFAULT 'M',
  `nat` char(10) DEFAULT NULL,
  `glider` varchar(100) DEFAULT NULL,
  `glider_cert` varchar(20) DEFAULT NULL,
  `parClass` varchar(50) DEFAULT NULL,
  `sponsor` varchar(100) DEFAULT NULL,
  `fai_valid` tinyint(1) NOT NULL DEFAULT '1',
  `fai_id` varchar(20) DEFAULT NULL,
  `xcontest_id` varchar(20) DEFAULT NULL,
  `live_id` varchar(10) DEFAULT NULL,
  `telegram_id` int(11) DEFAULT NULL,
  `team` varchar(100) DEFAULT NULL,
  `nat_team` tinyint(4) NOT NULL DEFAULT '1',
  `status` enum('confirmed','wild card','waiting list','cancelled','waiting for payment') DEFAULT NULL,
  `ranking` mediumint(9) DEFAULT NULL,
  `paid` tinyint(1) DEFAULT '0',
  `hours` smallint(6) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tblRanking`
--

CREATE TABLE `tblRanking` (
  `rank_id` int(11) NOT NULL,
  `rank_name` varchar(40) NOT NULL,
  `comp_class` enum('PG','HG','mixed') NOT NULL DEFAULT 'PG'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tblRegion`
--

CREATE TABLE `tblRegion` (
  `reg_id` int(11) NOT NULL,
  `comp_id` int(11) DEFAULT NULL,
  `centre` int(11) DEFAULT NULL,
  `radius` double DEFAULT NULL,
  `description` varchar(64) NOT NULL,
  `waypoint_file` varchar(50) NOT NULL,
  `openair_file` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tblRegionWaypoint`
--

CREATE TABLE `tblRegionWaypoint` (
  `rwp_id` int(11) NOT NULL,
  `reg_id` int(11) DEFAULT NULL,
  `name` varchar(12) NOT NULL,
  `lat` float NOT NULL,
  `lon` float NOT NULL,
  `altitude` smallint(6) NOT NULL,
  `description` varchar(64) DEFAULT NULL,
  `old` tinyint(1) NOT NULL DEFAULT '0',
  `xccSiteID` int(11) DEFAULT NULL,
  `xccToID` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tblRegionXCSites`
--

CREATE TABLE `tblRegionXCSites` (
  `reg_id` int(11) NOT NULL,
  `xccSiteID` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tblResultFile`
--

CREATE TABLE `tblResultFile` (
  `ref_id` int(11) NOT NULL,
  `comp_id` int(11) NOT NULL,
  `task_id` int(11) DEFAULT NULL,
  `created` int(11) NOT NULL,
  `filename` varchar(80) CHARACTER SET latin1 DEFAULT NULL,
  `status` varchar(255) CHARACTER SET latin1 DEFAULT NULL,
  `active` tinyint(1) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tblTask`
--

CREATE TABLE `tblTask` (
  `task_id` int(11) NOT NULL,
  `comp_id` int(11) DEFAULT NULL,
  `task_last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `task_num` tinyint(4) NOT NULL,
  `task_name` varchar(100) DEFAULT NULL,
  `date` date NOT NULL,
  `reg_id` int(11) DEFAULT NULL,
  `window_open_time` mediumint(9) DEFAULT NULL,
  `window_close_time` mediumint(9) DEFAULT NULL,
  `check_launch` enum('on','off') DEFAULT 'off',
  `start_time` mediumint(9) DEFAULT NULL,
  `start_close_time` mediumint(9) DEFAULT NULL,
  `SS_interval` smallint(6) NOT NULL DEFAULT '0',
  `start_iteration` tinyint(4) DEFAULT NULL,
  `task_deadline` mediumint(9) DEFAULT NULL,
  `stopped_time` mediumint(9) DEFAULT NULL,
  `tasResultsType` varchar(20) DEFAULT NULL,
  `task_type` enum('race','elapsed time','free distance','distance with bearing') DEFAULT 'race',
  `distance` float DEFAULT NULL,
  `opt_dist` float DEFAULT NULL,
  `opt_dist_to_SS` float DEFAULT NULL,
  `opt_dist_to_ESS` float DEFAULT NULL,
  `SS_distance` float DEFAULT NULL,
  `cancelled` tinyint(1) NOT NULL DEFAULT '0',
  `time_offset` mediumint(9) DEFAULT NULL,
  `formula_distance` enum('on','difficulty','off') DEFAULT NULL,
  `formula_departure` enum('leadout','departure','off') DEFAULT NULL,
  `formula_arrival` enum('position','time','off') DEFAULT NULL,
  `formula_time` enum('on','off') DEFAULT NULL,
  `arr_alt_bonus` float DEFAULT NULL,
  `max_JTG` smallint(6) DEFAULT NULL,
  `no_goal_penalty` float(4,3) DEFAULT NULL,
  `tolerance` float(6,5) DEFAULT NULL,
  `airspace_check` tinyint(1) DEFAULT NULL,
  `openair_file` varchar(40) DEFAULT NULL,
  `QNH` float(7,3) NOT NULL DEFAULT '1013.250',
  `comment` text,
  `locked` tinyint(3) NOT NULL DEFAULT '0',
  `task_path` varchar(40) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tblTaskResult`
--

CREATE TABLE `tblTaskResult` (
  `track_id` int(11) NOT NULL,
  `task_id` int(11) DEFAULT NULL,
  `par_id` int(11) DEFAULT NULL,
  `track_last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `track_file` varchar(255) DEFAULT NULL,
  `g_record` tinyint(4) DEFAULT '1',
  `distance_flown` double DEFAULT NULL,
  `best_distance_time` mediumint(9) DEFAULT '0',
  `stopped_distance` float DEFAULT '0',
  `stopped_altitude` smallint(6) DEFAULT '0',
  `total_distance` float DEFAULT '0',
  `first_time` mediumint(9) DEFAULT NULL,
  `real_start_time` mediumint(9) DEFAULT NULL,
  `SSS_time` mediumint(9) DEFAULT NULL,
  `ESS_time` mediumint(9) DEFAULT NULL,
  `goal_time` mediumint(9) DEFAULT NULL,
  `last_time` mediumint(9) DEFAULT NULL,
  `speed` double DEFAULT NULL,
  `waypoints_made` tinyint(4) DEFAULT NULL,
  `ESS_altitude` smallint(6) DEFAULT NULL,
  `goal_altitude` smallint(6) DEFAULT NULL,
  `max_altitude` smallint(6) DEFAULT NULL,
  `last_altitude` smallint(6) DEFAULT NULL,
  `landing_time` mediumint(9) DEFAULT NULL,
  `landing_altitude` smallint(6) DEFAULT NULL,
  `result_type` enum('abs','dnf','lo','goal','mindist','nyp') DEFAULT 'nyp',
  `penalty` double DEFAULT NULL,
  `comment` text,
  `place` smallint(6) DEFAULT NULL,
  `distance_score` double DEFAULT NULL,
  `time_score` double DEFAULT NULL,
  `arrival_score` double DEFAULT NULL,
  `departure_score` double DEFAULT NULL,
  `score` double DEFAULT NULL,
  `lead_coeff` double DEFAULT NULL,
  `fixed_LC` double DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tblTaskWaypoint`
--

CREATE TABLE `tblTaskWaypoint` (
  `wpt_id` int(11) NOT NULL,
  `task_id` int(11) DEFAULT NULL,
  `num` tinyint(4) NOT NULL,
  `name` char(6) NOT NULL,
  `rwp_id` int(11) DEFAULT NULL,
  `lat` float NOT NULL,
  `lon` float NOT NULL,
  `altitude` smallint(6) NOT NULL DEFAULT '0',
  `description` varchar(80) DEFAULT NULL,
  `time` mediumint(9) DEFAULT NULL,
  `type` enum('waypoint','launch','speed','endspeed','goal') DEFAULT 'waypoint',
  `how` enum('entry','exit') DEFAULT 'entry',
  `shape` enum('circle','semicircle','line') DEFAULT 'circle',
  `angle` smallint(6) DEFAULT NULL,
  `radius` mediumint(9) DEFAULT NULL,
  `ssr_lat` float DEFAULT NULL,
  `ssr_lon` float DEFAULT NULL,
  `partial_distance` double DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tblTrackWaypoint`
--

CREATE TABLE `tblTrackWaypoint` (
  `trw_id` int(11) NOT NULL,
  `track_id` int(11) NOT NULL,
  `wpt_id` int(11) DEFAULT NULL,
  `name` varchar(10) NOT NULL,
  `rawtime` mediumint(9) NOT NULL,
  `lat` float NOT NULL,
  `lon` float NOT NULL,
  `altitude` smallint(6) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tblUserSession`
--

CREATE TABLE `tblUserSession` (
  `user_id` int(11) NOT NULL,
  `user_session` varchar(128) DEFAULT NULL,
  `user_IP` varchar(32) DEFAULT NULL,
  `session_start` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `session_end` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tblXContestCodes`
--

CREATE TABLE `tblXContestCodes` (
  `xccSiteID` int(11) DEFAULT NULL,
  `xccSiteName` varchar(40) DEFAULT NULL,
  `xccToID` int(11) NOT NULL,
  `xccToName` varchar(40) NOT NULL,
  `xccAlt` int(11) DEFAULT NULL,
  `xccISO` varchar(2) NOT NULL,
  `xccCountryName` varchar(42) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Stand-in structure for view `TrackObjectView`
-- (See below for the actual view)
--
CREATE TABLE `TrackObjectView` (
`track_id` int(11)
,`par_id` int(11)
,`task_id` int(11)
,`civl_id` int(10)
,`glider` varchar(100)
,`glider_cert` varchar(20)
,`track_file` varchar(255)
);

-- --------------------------------------------------------

--
-- Stand-in structure for view `UnscoredPilotView`
-- (See below for the actual view)
--
CREATE TABLE `UnscoredPilotView` (
`task_id` int(11)
,`par_id` int(11)
,`comp_id` int(11)
,`civl_id` int(10)
,`fai_id` varchar(20)
,`pil_id` int(11)
,`ID` int(4)
,`name` varchar(50)
,`sex` enum('M','F')
,`nat` char(10)
,`glider` varchar(100)
,`glider_cert` varchar(20)
,`sponsor` varchar(100)
,`xcontest_id` varchar(20)
,`live_id` varchar(10)
,`team` varchar(100)
,`nat_team` tinyint(4)
);

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) UNSIGNED NOT NULL,
  `username` varchar(60) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci NOT NULL DEFAULT '',
  `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci NOT NULL DEFAULT '',
  `email` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci NOT NULL DEFAULT '',
  `created_at` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `first_name` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci,
  `last_name` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci,
  `nat` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci,
  `active` int(1) NOT NULL DEFAULT '0',
  `access` enum('pilot','scorekeeper','admin','pending') NOT NULL DEFAULT 'pilot'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Structure for view `CompObjectView`
--
DROP TABLE IF EXISTS `CompObjectView`;

CREATE ALGORITHM=UNDEFINED DEFINER=`lpp_db`@`66.33.192.0/255.255.224.0` SQL SECURITY DEFINER VIEW `CompObjectView`  AS  select `C`.`comp_id` AS `comp_id`,`C`.`comp_name` AS `comp_name`,`C`.`comp_site` AS `comp_site`,`C`.`date_from` AS `date_from`,`C`.`date_to` AS `date_to`,`C`.`MD_name` AS `MD_name`,`C`.`contact` AS `contact`,`C`.`cat_id` AS `cat_id`,`C`.`sanction` AS `sanction`,`C`.`comp_type` AS `comp_type`,`C`.`comp_code` AS `comp_code`,`C`.`restricted` AS `restricted`,`C`.`time_offset` AS `time_offset`,`C`.`comp_class` AS `comp_class`,`C`.`openair_file` AS `openair_file`,`C`.`stylesheet` AS `stylesheet`,`C`.`locked` AS `locked`,`C`.`comp_path` AS `comp_path`,`C`.`external` AS `external`,`C`.`website` AS `website`,`C`.`airspace_check` AS `airspace_check`,`C`.`check_launch` AS `check_launch`,`C`.`igc_config_file` AS `igc_config_file`,`C`.`self_register` AS `self_register`,`C`.`check_g_record` AS `check_g_record`,`FC`.`formula_type` AS `formula_type`,`FC`.`formula_version` AS `formula_version`,ifnull(`FC`.`external_name`,ifnull(`FC`.`formula_name`,concat(upper(`FC`.`formula_type`),`FC`.`formula_version`))) AS `formula_name`,`FC`.`overall_validity` AS `overall_validity`,`FC`.`validity_param` AS `validity_param`,`FC`.`validity_ref` AS `validity_ref`,`FC`.`nominal_goal` AS `nominal_goal`,`FC`.`min_dist` AS `min_dist`,`FC`.`nominal_dist` AS `nominal_dist`,`FC`.`nominal_time` AS `nominal_time`,`FC`.`nominal_launch` AS `nominal_launch`,`FC`.`formula_distance` AS `formula_distance`,`FC`.`formula_arrival` AS `formula_arrival`,`FC`.`formula_departure` AS `formula_departure`,`FC`.`lead_factor` AS `lead_factor`,`FC`.`formula_time` AS `formula_time`,`FC`.`no_goal_penalty` AS `no_goal_penalty`,`FC`.`glide_bonus` AS `glide_bonus`,`FC`.`tolerance` AS `tolerance`,`FC`.`min_tolerance` AS `min_tolerance`,`FC`.`arr_alt_bonus` AS `arr_alt_bonus`,`FC`.`arr_min_height` AS `arr_min_height`,`FC`.`arr_max_height` AS `arr_max_height`,`FC`.`validity_min_time` AS `validity_min_time`,`FC`.`score_back_time` AS `score_back_time`,`FC`.`max_JTG` AS `max_JTG`,`FC`.`JTG_penalty_per_sec` AS `JTG_penalty_per_sec`,`FC`.`scoring_altitude` AS `scoring_altitude`,`FC`.`task_result_decimal` AS `task_result_decimal`,`FC`.`comp_result_decimal` AS `comp_result_decimal`,`FC`.`team_scoring` AS `team_scoring`,`FC`.`team_size` AS `team_size`,`FC`.`max_team_size` AS `max_team_size`,`FC`.`country_scoring` AS `country_scoring`,`FC`.`country_size` AS `country_size`,`FC`.`max_country_size` AS `max_country_size`,`FC`.`team_over` AS `team_over` from (`tblCompetition` `C` left join `tblForComp` `FC` on((`C`.`comp_id` = `FC`.`comp_id`))) order by (case when (`C`.`comp_name` like '%test%') then `C`.`comp_name` else `C`.`date_to` end) desc ;

-- --------------------------------------------------------

--
-- Structure for view `FlightResultView`
--
DROP TABLE IF EXISTS `FlightResultView`;

CREATE ALGORITHM=UNDEFINED DEFINER=`lpp_db`@`66.33.192.0/255.255.224.0` SQL SECURITY DEFINER VIEW `FlightResultView`  AS  select `T`.`track_id` AS `track_id`,`T`.`par_id` AS `par_id`,`T`.`task_id` AS `task_id`,`R`.`comp_id` AS `comp_id`,`R`.`civl_id` AS `civl_id`,`R`.`fai_id` AS `fai_id`,`R`.`pil_id` AS `pil_id`,`R`.`ID` AS `ID`,`R`.`name` AS `name`,`R`.`nat` AS `nat`,`R`.`sex` AS `sex`,`R`.`glider` AS `glider`,`R`.`glider_cert` AS `glider_cert`,`R`.`sponsor` AS `sponsor`,`R`.`team` AS `team`,`R`.`nat_team` AS `nat_team`,`R`.`live_id` AS `live_id`,`T`.`distance_flown` AS `distance_flown`,`T`.`best_distance_time` AS `best_distance_time`,`T`.`stopped_distance` AS `stopped_distance`,`T`.`stopped_altitude` AS `stopped_altitude`,`T`.`total_distance` AS `total_distance`,`T`.`speed` AS `speed`,`T`.`first_time` AS `first_time`,`T`.`real_start_time` AS `real_start_time`,`T`.`goal_time` AS `goal_time`,`T`.`last_time` AS `last_time`,`T`.`result_type` AS `result_type`,`T`.`SSS_time` AS `SSS_time`,`T`.`ESS_time` AS `ESS_time`,`T`.`waypoints_made` AS `waypoints_made`,`T`.`penalty` AS `penalty`,`T`.`comment` AS `comment`,`T`.`time_score` AS `time_score`,`T`.`distance_score` AS `distance_score`,`T`.`arrival_score` AS `arrival_score`,`T`.`departure_score` AS `departure_score`,`T`.`score` AS `score`,`T`.`lead_coeff` AS `lead_coeff`,`T`.`fixed_LC` AS `fixed_LC`,`T`.`ESS_altitude` AS `ESS_altitude`,`T`.`goal_altitude` AS `goal_altitude`,`T`.`max_altitude` AS `max_altitude`,`T`.`last_altitude` AS `last_altitude`,`T`.`landing_altitude` AS `landing_altitude`,`T`.`landing_time` AS `landing_time`,`T`.`track_file` AS `track_file`,`T`.`g_record` AS `g_record` from (`tblTaskResult` `T` join `tblParticipant` `R` on((`T`.`par_id` = `R`.`par_id`))) order by `T`.`task_id`,`T`.`score` desc ;

-- --------------------------------------------------------

--
-- Structure for view `RegionWaypointView`
--
DROP TABLE IF EXISTS `RegionWaypointView`;

CREATE ALGORITHM=UNDEFINED DEFINER=`lpp_db`@`66.33.192.0/255.255.224.0` SQL SECURITY DEFINER VIEW `RegionWaypointView`  AS  select `tblRegionWaypoint`.`rwp_id` AS `rwp_id`,`tblRegionWaypoint`.`reg_id` AS `region_id`,`tblRegionWaypoint`.`name` AS `name`,`tblRegionWaypoint`.`lat` AS `lat`,`tblRegionWaypoint`.`lon` AS `lon`,`tblRegionWaypoint`.`altitude` AS `altitude`,`tblRegionWaypoint`.`description` AS `description` from `tblRegionWaypoint` where (`tblRegionWaypoint`.`old` = 0) ;

-- --------------------------------------------------------

--
-- Structure for view `TaskAirspaceCheckView`
--
DROP TABLE IF EXISTS `TaskAirspaceCheckView`;

CREATE ALGORITHM=UNDEFINED DEFINER=`lpp_db`@`66.33.192.0/255.255.224.0` SQL SECURITY DEFINER VIEW `TaskAirspaceCheckView`  AS  select `T`.`task_id` AS `task_id`,`T`.`airspace_check` AS `airspace_check`,`A`.`notification_distance` AS `notification_distance`,`A`.`function` AS `function`,`A`.`h_outer_limit` AS `h_outer_limit`,`A`.`h_inner_limit` AS `h_inner_limit`,`A`.`h_boundary` AS `h_boundary`,`A`.`h_boundary_penalty` AS `h_boundary_penalty`,`A`.`h_max_penalty` AS `h_max_penalty`,`A`.`v_outer_limit` AS `v_outer_limit`,`A`.`v_inner_limit` AS `v_inner_limit`,`A`.`v_boundary` AS `v_boundary`,`A`.`v_boundary_penalty` AS `v_boundary_penalty`,`A`.`v_max_penalty` AS `v_max_penalty` from ((`tblTask` `T` join `tblCompetition` `C` on((`T`.`comp_id` = `C`.`comp_id`))) left join `tblCompAirspaceCheck` `A` on((`T`.`comp_id` = `A`.`comp_id`))) order by `T`.`task_id` ;

-- --------------------------------------------------------

--
-- Structure for view `TaskFormulaView`
--
DROP TABLE IF EXISTS `TaskFormulaView`;

CREATE ALGORITHM=UNDEFINED DEFINER=`lpp_db`@`66.33.192.0/255.255.224.0` SQL SECURITY DEFINER VIEW `TaskFormulaView`  AS  select `FC`.`comp_id` AS `comp_id`,`T`.`task_id` AS `task_id`,`FC`.`formula_type` AS `formula_type`,`FC`.`formula_version` AS `formula_version`,ifnull(`FC`.`external_name`,ifnull(`FC`.`formula_name`,concat(upper(`FC`.`formula_type`),`FC`.`formula_version`))) AS `formula_name`,`FC`.`overall_validity` AS `overall_validity`,`FC`.`validity_param` AS `validity_param`,`FC`.`validity_ref` AS `validity_ref`,`FC`.`nominal_goal` AS `nominal_goal`,`FC`.`min_dist` AS `min_dist`,`FC`.`nominal_dist` AS `nominal_dist`,`FC`.`nominal_time` AS `nominal_time`,`FC`.`nominal_launch` AS `nominal_launch`,`T`.`formula_distance` AS `formula_distance`,`T`.`formula_departure` AS `formula_departure`,`T`.`formula_arrival` AS `formula_arrival`,`T`.`formula_time` AS `formula_time`,`FC`.`lead_factor` AS `lead_factor`,`T`.`no_goal_penalty` AS `no_goal_penalty`,`FC`.`glide_bonus` AS `glide_bonus`,`T`.`tolerance` AS `tolerance`,`FC`.`min_tolerance` AS `min_tolerance`,`T`.`arr_alt_bonus` AS `arr_alt_bonus`,`FC`.`arr_min_height` AS `arr_min_height`,`FC`.`arr_max_height` AS `arr_max_height`,`FC`.`validity_min_time` AS `validity_min_time`,`FC`.`score_back_time` AS `score_back_time`,`T`.`max_JTG` AS `max_JTG`,`FC`.`JTG_penalty_per_sec` AS `JTG_penalty_per_sec`,`FC`.`scoring_altitude` AS `scoring_altitude`,`FC`.`team_scoring` AS `team_scoring`,`FC`.`team_size` AS `team_size`,`FC`.`max_team_size` AS `max_team_size`,`FC`.`country_scoring` AS `country_scoring`,`FC`.`country_size` AS `country_size`,`FC`.`max_country_size` AS `max_country_size` from (`tblTask` `T` join `tblForComp` `FC` on((`T`.`comp_id` = `FC`.`comp_id`))) order by `T`.`task_id` ;

-- --------------------------------------------------------

--
-- Structure for view `TaskObjectView`
--
DROP TABLE IF EXISTS `TaskObjectView`;

CREATE ALGORITHM=UNDEFINED DEFINER=`lpp_db`@`66.33.192.0/255.255.224.0` SQL SECURITY DEFINER VIEW `TaskObjectView`  AS  select `T`.`task_id` AS `task_id`,`C`.`comp_code` AS `comp_code`,`C`.`comp_name` AS `comp_name`,`C`.`comp_site` AS `comp_site`,`T`.`time_offset` AS `time_offset`,`C`.`comp_class` AS `comp_class`,`T`.`comp_id` AS `comp_id`,`T`.`date` AS `date`,`T`.`task_name` AS `task_name`,`T`.`task_num` AS `task_num`,`T`.`reg_id` AS `reg_id`,`R`.`description` AS `region_name`,`T`.`window_open_time` AS `window_open_time`,`T`.`task_deadline` AS `task_deadline`,`T`.`window_close_time` AS `window_close_time`,`T`.`check_launch` AS `check_launch`,`T`.`start_time` AS `start_time`,`T`.`SS_interval` AS `SS_interval`,`T`.`start_iteration` AS `start_iteration`,`T`.`start_close_time` AS `start_close_time`,`T`.`stopped_time` AS `stopped_time`,upper(`T`.`task_type`) AS `task_type`,`T`.`distance` AS `distance`,`T`.`opt_dist` AS `opt_dist`,`T`.`opt_dist_to_SS` AS `opt_dist_to_SS`,`T`.`opt_dist_to_ESS` AS `opt_dist_to_ESS`,`T`.`SS_distance` AS `SS_distance`,`T`.`QNH` AS `QNH`,`T`.`comment` AS `comment`,`T`.`locked` AS `locked`,`T`.`airspace_check` AS `airspace_check`,`T`.`openair_file` AS `openair_file`,`T`.`cancelled` AS `cancelled`,`C`.`track_source` AS `track_source`,`T`.`task_path` AS `task_path`,`C`.`comp_path` AS `comp_path`,`C`.`igc_config_file` AS `igc_config_file` from ((`tblTask` `T` join `tblCompetition` `C` on((`T`.`comp_id` = `C`.`comp_id`))) left join `tblRegion` `R` on((`T`.`reg_id` = `R`.`reg_id`))) order by `T`.`date` ;

-- --------------------------------------------------------

--
-- Structure for view `TrackObjectView`
--
DROP TABLE IF EXISTS `TrackObjectView`;

CREATE ALGORITHM=UNDEFINED DEFINER=`lpp_db`@`66.33.192.0/255.255.224.0` SQL SECURITY DEFINER VIEW `TrackObjectView`  AS  select `T`.`track_id` AS `track_id`,`T`.`par_id` AS `par_id`,`T`.`task_id` AS `task_id`,`R`.`civl_id` AS `civl_id`,`R`.`glider` AS `glider`,`R`.`glider_cert` AS `glider_cert`,`T`.`track_file` AS `track_file` from (`tblTaskResult` `T` join `tblParticipant` `R` on((`T`.`par_id` = `R`.`par_id`))) where (`T`.`track_file` is not null) order by `T`.`track_id` ;

-- --------------------------------------------------------

--
-- Structure for view `UnscoredPilotView`
--
DROP TABLE IF EXISTS `UnscoredPilotView`;

CREATE ALGORITHM=UNDEFINED DEFINER=`lpp_db`@`66.33.192.0/255.255.224.0` SQL SECURITY DEFINER VIEW `UnscoredPilotView`  AS  select `T`.`task_id` AS `task_id`,`R`.`par_id` AS `par_id`,`R`.`comp_id` AS `comp_id`,`R`.`civl_id` AS `civl_id`,`R`.`fai_id` AS `fai_id`,`R`.`pil_id` AS `pil_id`,`R`.`ID` AS `ID`,`R`.`name` AS `name`,`R`.`sex` AS `sex`,`R`.`nat` AS `nat`,`R`.`glider` AS `glider`,`R`.`glider_cert` AS `glider_cert`,`R`.`sponsor` AS `sponsor`,`R`.`xcontest_id` AS `xcontest_id`,`R`.`live_id` AS `live_id`,`R`.`team` AS `team`,`R`.`nat_team` AS `nat_team` from ((`tblParticipant` `R` join `tblTask` `T` on((`R`.`comp_id` = `T`.`comp_id`))) left join `tblTaskResult` `TR` on(((`T`.`task_id` = `TR`.`task_id`) and (`R`.`par_id` = `TR`.`par_id`)))) where isnull(`TR`.`track_id`) order by `T`.`task_id`,`R`.`par_id` ;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `tblCertification`
--
ALTER TABLE `tblCertification`
  ADD PRIMARY KEY (`cert_id`);

--
-- Indexes for table `tblClasCertRank`
--
ALTER TABLE `tblClasCertRank`
  ADD KEY `ccr_cla_foreign` (`cat_id`),
  ADD KEY `ccr_cert_foreign` (`cert_id`),
  ADD KEY `ccr_rank_foreign` (`rank_id`);

--
-- Indexes for table `tblClassification`
--
ALTER TABLE `tblClassification`
  ADD PRIMARY KEY (`cat_id`);

--
-- Indexes for table `tblCompAirspaceCheck`
--
ALTER TABLE `tblCompAirspaceCheck`
  ADD UNIQUE KEY `comp_id` (`comp_id`);

--
-- Indexes for table `tblCompetition`
--
ALTER TABLE `tblCompetition`
  ADD PRIMARY KEY (`comp_id`) USING BTREE,
  ADD UNIQUE KEY `comp_id` (`comp_id`,`comp_name`),
  ADD KEY `cla_foreign` (`cat_id`);

--
-- Indexes for table `tblCountryCode`
--
ALTER TABLE `tblCountryCode`
  ADD PRIMARY KEY (`natId`);

--
-- Indexes for table `tblForComp`
--
ALTER TABLE `tblForComp`
  ADD PRIMARY KEY (`comp_id`);

--
-- Indexes for table `tblLadder`
--
ALTER TABLE `tblLadder`
  ADD PRIMARY KEY (`ladder_id`);

--
-- Indexes for table `tblLadderComp`
--
ALTER TABLE `tblLadderComp`
  ADD KEY `ladder_foreign` (`ladder_id`),
  ADD KEY `comp_foreign` (`comp_id`);

--
-- Indexes for table `tblLadderSeason`
--
ALTER TABLE `tblLadderSeason`
  ADD KEY `season_cla_foreign` (`cat_id`),
  ADD KEY `season_lad_foreign` (`ladder_id`),
  ADD KEY `seasonYear` (`season`);

--
-- Indexes for table `tblNotification`
--
ALTER TABLE `tblNotification`
  ADD PRIMARY KEY (`not_id`),
  ADD KEY `track_id` (`track_id`);

--
-- Indexes for table `tblParticipant`
--
ALTER TABLE `tblParticipant`
  ADD PRIMARY KEY (`par_id`),
  ADD KEY `par_pil_id` (`pil_id`,`comp_id`),
  ADD KEY `civl_id` (`civl_id`);

--
-- Indexes for table `tblRanking`
--
ALTER TABLE `tblRanking`
  ADD PRIMARY KEY (`rank_id`);

--
-- Indexes for table `tblRegion`
--
ALTER TABLE `tblRegion`
  ADD PRIMARY KEY (`reg_id`);

--
-- Indexes for table `tblRegionWaypoint`
--
ALTER TABLE `tblRegionWaypoint`
  ADD PRIMARY KEY (`rwp_id`),
  ADD KEY `region_foreign` (`reg_id`);

--
-- Indexes for table `tblRegionXCSites`
--
ALTER TABLE `tblRegionXCSites`
  ADD KEY `xc_region_foreign` (`reg_id`),
  ADD KEY `xccSiteID` (`xccSiteID`);

--
-- Indexes for table `tblResultFile`
--
ALTER TABLE `tblResultFile`
  ADD PRIMARY KEY (`ref_id`),
  ADD KEY `filename` (`filename`);

--
-- Indexes for table `tblTask`
--
ALTER TABLE `tblTask`
  ADD PRIMARY KEY (`task_id`),
  ADD KEY `task_comp_id` (`comp_id`),
  ADD KEY `foreign_regPk` (`reg_id`);

--
-- Indexes for table `tblTaskResult`
--
ALTER TABLE `tblTaskResult`
  ADD PRIMARY KEY (`track_id`),
  ADD UNIQUE KEY `track_id` (`track_id`,`task_id`,`par_id`) USING BTREE,
  ADD KEY `res_task_id` (`task_id`),
  ADD KEY `res_par_id` (`par_id`) USING BTREE;

--
-- Indexes for table `tblTaskWaypoint`
--
ALTER TABLE `tblTaskWaypoint`
  ADD PRIMARY KEY (`wpt_id`),
  ADD KEY `idx_tblTaskWaypoint_tawType` (`type`),
  ADD KEY `tasPk` (`task_id`);

--
-- Indexes for table `tblTrackWaypoint`
--
ALTER TABLE `tblTrackWaypoint`
  ADD PRIMARY KEY (`trw_id`),
  ADD KEY `track` (`track_id`);

--
-- Indexes for table `tblXContestCodes`
--
ALTER TABLE `tblXContestCodes`
  ADD PRIMARY KEY (`xccToID`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `tblCertification`
--
ALTER TABLE `tblCertification`
  MODIFY `cert_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `tblClassification`
--
ALTER TABLE `tblClassification`
  MODIFY `cat_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `tblCompetition`
--
ALTER TABLE `tblCompetition`
  MODIFY `comp_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `tblLadder`
--
ALTER TABLE `tblLadder`
  MODIFY `ladder_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `tblNotification`
--
ALTER TABLE `tblNotification`
  MODIFY `not_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `tblParticipant`
--
ALTER TABLE `tblParticipant`
  MODIFY `par_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `tblRanking`
--
ALTER TABLE `tblRanking`
  MODIFY `rank_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `tblRegion`
--
ALTER TABLE `tblRegion`
  MODIFY `reg_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `tblRegionWaypoint`
--
ALTER TABLE `tblRegionWaypoint`
  MODIFY `rwp_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `tblResultFile`
--
ALTER TABLE `tblResultFile`
  MODIFY `ref_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `tblTask`
--
ALTER TABLE `tblTask`
  MODIFY `task_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `tblTaskResult`
--
ALTER TABLE `tblTaskResult`
  MODIFY `track_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `tblTaskWaypoint`
--
ALTER TABLE `tblTaskWaypoint`
  MODIFY `wpt_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `tblTrackWaypoint`
--
ALTER TABLE `tblTrackWaypoint`
  MODIFY `trw_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
