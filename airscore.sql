USE airscore

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";
SET NAMES utf8mb4;

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
,`track_source` varchar(40)
,`formula_name` varchar(50)
,`overall_validity` enum('ftv','all','round')
,`validity_param` decimal(4,3)
,`validity_ref` enum('day_quality','max_score')
,`nominal_goal` decimal(3,2)
,`min_dist` mediumint(9)
,`nominal_dist` mediumint(9)
,`nominal_time` smallint(6)
,`nominal_launch` decimal(3,2)
,`formula_distance` enum('on','difficulty','off')
,`formula_arrival` enum('position','time','off')
,`formula_departure` enum('leadout','departure','off')
,`lead_factor` decimal(4,2)
,`formula_time` enum('on','off')
,`no_goal_penalty` decimal(4,3)
,`glide_bonus` decimal(4,2)
,`tolerance` decimal(6,5)
,`min_tolerance` int(4)
,`arr_alt_bonus` float
,`arr_min_height` smallint(6)
,`arr_max_height` smallint(6)
,`validity_min_time` smallint(6)
,`score_back_time` smallint(6)
,`max_JTG` smallint(6)
,`JTG_penalty_per_sec` decimal(4,2)
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
,`sponsor` varchar(500)
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Stand-in structure for view `RegionWaypointView`
-- (See below for the actual view)
--
CREATE TABLE `RegionWaypointView` (
`rwp_id` int(11)
,`region_id` int(11)
,`name` varchar(12)
,`lat` decimal(8,6)
,`lon` decimal(9,6)
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Stand-in structure for view `TaskFormulaView`
-- (See below for the actual view)
--
CREATE TABLE `TaskFormulaView` (
`comp_id` int(11)
,`task_id` int(11)
,`formula_name` varchar(50)
,`overall_validity` enum('ftv','all','round')
,`validity_param` decimal(4,3)
,`validity_ref` enum('day_quality','max_score')
,`nominal_goal` decimal(3,2)
,`min_dist` mediumint(9)
,`nominal_dist` mediumint(9)
,`nominal_time` smallint(6)
,`nominal_launch` decimal(3,2)
,`formula_distance` enum('on','difficulty','off')
,`formula_departure` enum('leadout','departure','off')
,`formula_arrival` enum('position','time','off')
,`formula_time` enum('on','off')
,`lead_factor` decimal(4,2)
,`no_goal_penalty` decimal(4,3)
,`glide_bonus` decimal(4,2)
,`tolerance` decimal(6,5)
,`min_tolerance` int(4)
,`arr_alt_bonus` float
,`arr_min_height` smallint(6)
,`arr_max_height` smallint(6)
,`validity_min_time` smallint(6)
,`score_back_time` smallint(6)
,`max_JTG` smallint(6)
,`JTG_penalty_per_sec` decimal(4,2)
,`scoring_altitude` enum('GPS','QNH')
,`task_result_decimal` int(4)
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
,`QNH` decimal(7,3)
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
  `comp_class` enum('PG','HG','mixed') NOT NULL DEFAULT 'PG',
  `cert_order` tinyint NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO tblCertification (cert_id, cert_name, comp_class, cert_order) VALUES
(1, 'A', 'PG', 1),
(2, 'B', 'PG', 2),
(3, 'C', 'PG', 3),
(4, 'D', 'PG', 4),
(5, 'CCC', 'PG', 5),
(6, 'Class 1', 'HG', 1),
(7, 'Class 5', 'HG', 2);

-- --------------------------------------------------------

--
-- Table structure for table `tblAirspaceCheck`
--

CREATE TABLE `tblAirspaceCheck` (
  `check_id` int NOT NULL,
  `comp_id` int NOT NULL,
  `task_id` int DEFAULT NULL,
  `notification_distance` smallint NOT NULL DEFAULT '100',
  `function` enum('linear','non-linear') COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'linear',
  `h_outer_limit` smallint NOT NULL DEFAULT '70',
  `h_boundary` smallint NOT NULL DEFAULT '0',
  `h_boundary_penalty` decimal(3,2) NOT NULL DEFAULT '0.10',
  `h_inner_limit` smallint NOT NULL DEFAULT '-30',
  `h_max_penalty` decimal(3,2) NOT NULL DEFAULT '1.00',
  `v_outer_limit` smallint NOT NULL DEFAULT '70',
  `v_boundary` smallint NOT NULL DEFAULT '0',
  `v_boundary_penalty` decimal(3,2) NOT NULL DEFAULT '0.10',
  `v_inner_limit` smallint NOT NULL DEFAULT '-30',
  `v_max_penalty` decimal(3,2) NOT NULL DEFAULT '1.00'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `tblCompAuth`
--

CREATE TABLE `tblCompAuth` (
  `user_id` int(11) NOT NULL,
  `comp_id` int(11) NOT NULL,
  `user_auth` enum('read','write','admin','owner') NOT NULL DEFAULT 'read'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `tblCompetition`
--

CREATE TABLE `tblCompetition` (
  `comp_id` int(11) NOT NULL,
  `comp_name` varchar(100) NOT NULL,
  `comp_code` varchar(10) DEFAULT NULL,
  `comp_class` enum('PG','HG','mixed') DEFAULT 'PG',
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `comp_site` varchar(100) NOT NULL,
  `date_from` date NOT NULL,
  `date_to` date NOT NULL,
  `time_offset` mediumint(9) NOT NULL DEFAULT '0',
  `MD_name` varchar(100) DEFAULT NULL,
  `contact` varchar(100) DEFAULT NULL,
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `tblCompAttribute`
--

CREATE TABLE `tblCompAttribute` (
  `attr_id` int NOT NULL,
  `comp_id` int NOT NULL,
  `attr_key` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `attr_value` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `tblCompRanking`
--

CREATE TABLE `tblCompRanking` (
  `rank_id` int NOT NULL,
  `comp_id` int NOT NULL,
  `rank_name` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `rank_type` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'cert',
  `cert_id` int DEFAULT NULL,
  `min_date` date DEFAULT NULL,
  `max_date` date DEFAULT NULL,
  `attr_id` int DEFAULT NULL,
  `rank_value` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `tblForComp`
--

CREATE TABLE `tblForComp` (
  `comp_id` int(11) NOT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `formula_name` varchar(20) DEFAULT NULL,
  `overall_validity` enum('ftv','all','round') NOT NULL DEFAULT 'ftv',
  `validity_param` decimal(4,3) NOT NULL DEFAULT '0.750',
  `validity_ref` enum('day_quality','max_score') DEFAULT 'max_score',
  `nominal_goal` decimal(3,2) NOT NULL DEFAULT '0.30',
  `min_dist` mediumint(9) NOT NULL DEFAULT '5000',
  `nominal_dist` mediumint(9) NOT NULL DEFAULT '45000',
  `nominal_time` smallint(6) NOT NULL DEFAULT '5400',
  `nominal_launch` decimal(3,2) NOT NULL DEFAULT '0.96',
  `formula_distance` enum('on','difficulty','off') NOT NULL DEFAULT 'on',
  `formula_arrival` enum('position','time','off') NOT NULL DEFAULT 'off',
  `formula_departure` enum('leadout','departure','off') NOT NULL DEFAULT 'leadout',
  `lead_factor` decimal(4,2) NOT NULL DEFAULT '1.00',
  `formula_time` enum('on','off') NOT NULL DEFAULT 'on',
  `no_goal_penalty` decimal(4,3) NOT NULL DEFAULT '1.000',
  `glide_bonus` decimal(4,2) NOT NULL DEFAULT '4.00',
  `tolerance` decimal(6,5) NOT NULL DEFAULT '0.10000',
  `min_tolerance` int(4) NOT NULL DEFAULT '5',
  `arr_alt_bonus` float NOT NULL DEFAULT '0',
  `arr_min_height` smallint(6) DEFAULT NULL,
  `arr_max_height` smallint(6) DEFAULT NULL,
  `validity_min_time` smallint(6) DEFAULT NULL,
  `score_back_time` smallint(6) NOT NULL DEFAULT '300',
  `max_JTG` smallint(6) NOT NULL DEFAULT '0',
  `JTG_penalty_per_sec` decimal(4,2) DEFAULT NULL,
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `tblLadder`
--

CREATE TABLE `tblLadder` (
  `ladder_id` int NOT NULL,
  `ladder_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `ladder_class` enum('PG','HG') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'PG',
  `nat` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `date_from` date DEFAULT NULL,
  `date_to` date DEFAULT NULL,
  `external` tinyint(1) DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `tblLadderRanking`
--

CREATE TABLE `tblLadderRanking` (
  `rank_id` int NOT NULL,
  `ladder_id` int NOT NULL,
  `rank_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `rank_type` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'cert',
  `cert_id` int DEFAULT NULL,
  `min_date` date DEFAULT NULL,
  `max_date` date DEFAULT NULL,
  `rank_key` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `rank_value` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------
--
-- Table structure for table `tblCountryCode`
--

CREATE TABLE `tblCountryCode` (
  `natName` varchar(52) NOT NULL,
  `natIso2` varchar(2) NOT NULL,
  `natIso3` varchar(3) NOT NULL,
  `natId` int(11) NOT NULL,
  `natIoc` varchar(3) DEFAULT NULL,
  `natRegion` varchar(8) DEFAULT NULL,
  `natSubRegion` varchar(25) DEFAULT NULL,
  `natRegionId` int(11) DEFAULT NULL,
  `natSubRegionId` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `tblCountryCode`
--

INSERT INTO `tblCountryCode` (`natName`, `natIso2`, `natIso3`, `natId`, `natIoc`, `natRegion`, `natSubRegion`, `natRegionId`, `natSubRegionId`) VALUES
('Afghanistan', 'AF', 'AFG', 4, 'AFG', 'Asia', 'Southern Asia', 142, 34),
('Albania', 'AL', 'ALB', 8, 'ALB', 'Europe', 'Southern Europe', 150, 39),
('Antarctica', 'AQ', 'ATA', 10, NULL, NULL, NULL, NULL, NULL),
('Algeria', 'DZ', 'DZA', 12, 'ALG', 'Africa', 'Northern Africa', 2, 15),
('American Samoa', 'AS', 'ASM', 16, 'ASA', 'Oceania', 'Polynesia', 9, 61),
('Andorra', 'AD', 'AND', 20, 'AND', 'Europe', 'Southern Europe', 150, 39),
('Angola', 'AO', 'AGO', 24, 'ANG', 'Africa', 'Middle Africa', 2, 17),
('Antigua and Barbuda', 'AG', 'ATG', 28, 'ANT', 'Americas', 'Caribbean', 19, 29),
('Azerbaijan', 'AZ', 'AZE', 31, 'AZE', 'Asia', 'Western Asia', 142, 145),
('Argentina', 'AR', 'ARG', 32, 'ARG', 'Americas', 'South America', 19, 5),
('Australia', 'AU', 'AUS', 36, 'AUS', 'Oceania', 'Australia and New Zealand', 9, 53),
('Austria', 'AT', 'AUT', 40, 'AUT', 'Europe', 'Western Europe', 150, 155),
('Bahamas', 'BS', 'BHS', 44, 'BAH', 'Americas', 'Caribbean', 19, 29),
('Bahrain', 'BH', 'BHR', 48, 'BRN', 'Asia', 'Western Asia', 142, 145),
('Bangladesh', 'BD', 'BGD', 50, 'BAN', 'Asia', 'Southern Asia', 142, 34),
('Armenia', 'AM', 'ARM', 51, 'ARM', 'Asia', 'Western Asia', 142, 145),
('Barbados', 'BB', 'BRB', 52, 'BAR', 'Americas', 'Caribbean', 19, 29),
('Belgium', 'BE', 'BEL', 56, 'BEL', 'Europe', 'Western Europe', 150, 155),
('Bermuda', 'BM', 'BMU', 60, 'BER', 'Americas', 'Northern America', 19, 21),
('Bhutan', 'BT', 'BTN', 64, 'BHU', 'Asia', 'Southern Asia', 142, 34),
('Bolivia', 'BO', 'BOL', 68, 'BOL', 'Americas', 'South America', 19, 5),
('Bosnia and Herzegovina', 'BA', 'BIH', 70, 'BIH', 'Europe', 'Southern Europe', 150, 39),
('Botswana', 'BW', 'BWA', 72, 'BOT', 'Africa', 'Southern Africa', 2, 18),
('Bouvet Island', 'BV', 'BVT', 74, NULL, NULL, NULL, NULL, NULL),
('Brazil', 'BR', 'BRA', 76, 'BRA', 'Americas', 'South America', 19, 5),
('Belize', 'BZ', 'BLZ', 84, 'BIZ', 'Americas', 'Central America', 19, 13),
('British Indian Ocean Territory', 'IO', 'IOT', 86, NULL, NULL, NULL, NULL, NULL),
('Solomon Islands', 'SB', 'SLB', 90, 'SOL', 'Oceania', 'Melanesia', 9, 54),
('British Virgin Islands', 'VG', 'VGB', 92, 'IVB', 'Americas', 'Caribbean', 19, 29),
('Brunei', 'BN', 'BRN', 96, 'BRU', 'Asia', 'South-Eastern Asia', 142, 35),
('Bulgaria', 'BG', 'BGR', 100, 'BUL', 'Europe', 'Eastern Europe', 150, 151),
('Burma', 'MM', 'MMR', 104, 'MYA', 'Asia', 'South-Eastern Asia', 142, 35),
('Burundi', 'BI', 'BDI', 108, 'BDI', 'Africa', 'Eastern Africa', 2, 14),
('Belarus', 'BY', 'BLR', 112, 'BLR', 'Europe', 'Eastern Europe', 150, 151),
('Cambodia', 'KH', 'KHM', 116, 'CAM', 'Asia', 'South-Eastern Asia', 142, 35),
('Cameroon', 'CM', 'CMR', 120, 'CMR', 'Africa', 'Middle Africa', 2, 17),
('Canada', 'CA', 'CAN', 124, 'CAN', 'Americas', 'Northern America', 19, 21),
('Cape Verde', 'CV', 'CPV', 132, 'CPV', 'Africa', 'Western Africa', 2, 11),
('Cayman Islands', 'KY', 'CYM', 136, 'CAY', 'Americas', 'Caribbean', 19, 29),
('Central African Republic', 'CF', 'CAF', 140, 'CAF', 'Africa', 'Middle Africa', 2, 17),
('Sri Lanka', 'LK', 'LKA', 144, 'SRI', 'Asia', 'Southern Asia', 142, 34),
('Chad', 'TD', 'TCD', 148, 'CHA', 'Africa', 'Middle Africa', 2, 17),
('Chile', 'CL', 'CHL', 152, 'CHI', 'Americas', 'South America', 19, 5),
('China', 'CN', 'CHN', 156, 'CHN', 'Asia', 'Eastern Asia', 142, 30),
('Taiwan', 'TW', 'TWN', 158, 'TPE', 'Asia', 'Eastern Asia', 142, 30),
('Christmas Island', 'CX', 'CXR', 162, NULL, NULL, NULL, NULL, NULL),
('Cocos (Keeling) Islands', 'CC', 'CCK', 166, NULL, NULL, NULL, NULL, NULL),
('Colombia', 'CO', 'COL', 170, 'COL', 'Americas', 'South America', 19, 5),
('Comoros', 'KM', 'COM', 174, 'COM', 'Africa', 'Eastern Africa', 2, 14),
('Mayotte', 'YT', 'MYT', 175, NULL, 'Africa', 'Eastern Africa', 2, 14),
('Republic of the Congo', 'CG', 'COG', 178, 'CGO', 'Africa', 'Middle Africa', 2, 17),
('Democratic Republic of the Congo', 'CD', 'COD', 180, 'COD', 'Africa', 'Middle Africa', 2, 17),
('Cook Islands', 'CK', 'COK', 184, 'COK', 'Oceania', 'Polynesia', 9, 61),
('Costa Rica', 'CR', 'CRI', 188, 'CRC', 'Americas', 'Central America', 19, 13),
('Croatia', 'HR', 'HRV', 191, 'CRO', 'Europe', 'Southern Europe', 150, 39),
('Cuba', 'CU', 'CUB', 192, 'CUB', 'Americas', 'Caribbean', 19, 29),
('Cyprus', 'CY', 'CYP', 196, 'CYP', 'Asia', 'Western Asia', 142, 145),
('Czechia', 'CZ', 'CZE', 203, 'CZE', 'Europe', 'Eastern Europe', 150, 151),
('Benin', 'BJ', 'BEN', 204, 'BEN', 'Africa', 'Western Africa', 2, 11),
('Denmark', 'DK', 'DNK', 208, 'DEN', 'Europe', 'Northern Europe', 150, 154),
('Dominica', 'DM', 'DMA', 212, 'DMA', 'Americas', 'Caribbean', 19, 29),
('Dominican Republic', 'DO', 'DOM', 214, 'DOM', 'Americas', 'Caribbean', 19, 29),
('Ecuador', 'EC', 'ECU', 218, 'ECU', 'Americas', 'South America', 19, 5),
('El Salvador', 'SV', 'SLV', 222, 'ESA', 'Americas', 'Central America', 19, 13),
('Equatorial Guinea', 'GQ', 'GNQ', 226, 'GEQ', 'Africa', 'Middle Africa', 2, 17),
('Ethiopia', 'ET', 'ETH', 231, 'ETH', 'Africa', 'Eastern Africa', 2, 14),
('Eritrea', 'ER', 'ERI', 232, 'ERI', 'Africa', 'Eastern Africa', 2, 14),
('Estonia', 'EE', 'EST', 233, 'EST', 'Europe', 'Northern Europe', 150, 154),
('Faroe Islands', 'FO', 'FRO', 234, NULL, 'Europe', 'Northern Europe', 150, 154),
('Falkland Islands', 'FK', 'FLK', 238, NULL, 'Americas', 'South America', 19, 5),
('South Georgia and South Sandwich Islands', 'GS', 'SGS', 239, NULL, NULL, NULL, NULL, NULL),
('Fiji', 'FJ', 'FJI', 242, 'FIJ', 'Oceania', 'Melanesia', 9, 54),
('Finland', 'FI', 'FIN', 246, 'FIN', 'Europe', 'Northern Europe', 150, 154),
('Åland Islands', 'AX', 'ALA', 248, NULL, 'Europe', 'Northern Europe', 150, 154),
('France', 'FR', 'FRA', 250, 'FRA', 'Europe', 'Western Europe', 150, 155),
('French Guiana', 'GF', 'GUF', 254, NULL, 'Americas', 'South America', 19, 5),
('French Polynesia', 'PF', 'PYF', 258, NULL, 'Oceania', 'Polynesia', 9, 61),
('French Southern and Antarctic Lands', 'TF', 'ATF', 260, NULL, NULL, NULL, NULL, NULL),
('Djibouti', 'DJ', 'DJI', 262, 'DJI', 'Africa', 'Eastern Africa', 2, 14),
('Gabon', 'GA', 'GAB', 266, 'GAB', 'Africa', 'Middle Africa', 2, 17),
('Georgia', 'GE', 'GEO', 268, 'GEO', 'Asia', 'Western Asia', 142, 145),
('Gambia', 'GM', 'GMB', 270, 'GAM', 'Africa', 'Western Africa', 2, 11),
('Palestine', 'PS', 'PSE', 275, 'PLE', 'Asia', 'Western Asia', 142, 145),
('Germany', 'DE', 'DEU', 276, 'GER', 'Europe', 'Western Europe', 150, 155),
('Ghana', 'GH', 'GHA', 288, 'GHA', 'Africa', 'Western Africa', 2, 11),
('Gibraltar', 'GI', 'GIB', 292, NULL, 'Europe', 'Southern Europe', 150, 39),
('Kiribati', 'KI', 'KIR', 296, 'KIR', 'Oceania', 'Micronesia', 9, 57),
('Greece', 'GR', 'GRC', 300, 'GRE', 'Europe', 'Southern Europe', 150, 39),
('Greenland', 'GL', 'GRL', 304, NULL, 'Americas', 'Northern America', 19, 21),
('Grenada', 'GD', 'GRD', 308, 'GRN', 'Americas', 'Caribbean', 19, 29),
('Guadeloupe', 'GP', 'GLP', 312, NULL, 'Americas', 'Caribbean', 19, 29),
('Guam', 'GU', 'GUM', 316, 'GUM', 'Oceania', 'Micronesia', 9, 57),
('Guatemala', 'GT', 'GTM', 320, 'GUA', 'Americas', 'Central America', 19, 13),
('Guinea', 'GN', 'GIN', 324, 'GUI', 'Africa', 'Western Africa', 2, 11),
('Guyana', 'GY', 'GUY', 328, 'GUY', 'Americas', 'South America', 19, 5),
('Haiti', 'HT', 'HTI', 332, 'HAI', 'Americas', 'Caribbean', 19, 29),
('Heard Island and McDonald Islands', 'HM', 'HMD', 334, NULL, NULL, NULL, NULL, NULL),
('Holy See (Vatican City)', 'VA', 'VAT', 336, NULL, 'Europe', 'Southern Europe', 150, 39),
('Honduras', 'HN', 'HND', 340, 'HON', 'Americas', 'Central America', 19, 13),
('Hong Kong', 'HK', 'HKG', 344, 'HKG', 'Asia', 'Eastern Asia', 142, 30),
('Hungary', 'HU', 'HUN', 348, 'HUN', 'Europe', 'Eastern Europe', 150, 151),
('Iceland', 'IS', 'ISL', 352, 'ISL', 'Europe', 'Northern Europe', 150, 154),
('India', 'IN', 'IND', 356, 'IND', 'Asia', 'Southern Asia', 142, 34),
('Indonesia', 'ID', 'IDN', 360, 'INA', 'Asia', 'South-Eastern Asia', 142, 35),
('Iran', 'IR', 'IRN', 364, 'IRI', 'Asia', 'Southern Asia', 142, 34),
('Iraq', 'IQ', 'IRQ', 368, 'IRQ', 'Asia', 'Western Asia', 142, 145),
('Ireland', 'IE', 'IRL', 372, 'IRL', 'Europe', 'Northern Europe', 150, 154),
('Israel', 'IL', 'ISR', 376, 'ISR', 'Asia', 'Western Asia', 142, 145),
('Italy', 'IT', 'ITA', 380, 'ITA', 'Europe', 'Southern Europe', 150, 39),
('Ivory Coast', 'CI', 'CIV', 384, 'CIV', 'Africa', 'Western Africa', 2, 11),
('Jamaica', 'JM', 'JAM', 388, 'JAM', 'Americas', 'Caribbean', 19, 29),
('Japan', 'JP', 'JPN', 392, 'JPN', 'Asia', 'Eastern Asia', 142, 30),
('Kazakhstan', 'KZ', 'KAZ', 398, 'KAZ', 'Asia', 'Central Asia', 142, 143),
('Jordan', 'JO', 'JOR', 400, 'JOR', 'Asia', 'Western Asia', 142, 145),
('Kenya', 'KE', 'KEN', 404, 'KEN', 'Africa', 'Eastern Africa', 2, 14),
('North Korea', 'KP', 'PRK', 408, 'PRK', 'Asia', 'Eastern Asia', 142, 30),
('South Korea', 'KR', 'KOR', 410, 'KOR', 'Asia', 'Eastern Asia', 142, 30),
('Kuwait', 'KW', 'KWT', 414, 'KUW', 'Asia', 'Western Asia', 142, 145),
('Kyrgyzstan', 'KG', 'KGZ', 417, 'KGZ', 'Asia', 'Central Asia', 142, 143),
('Laos', 'LA', 'LAO', 418, 'LAO', 'Asia', 'South-Eastern Asia', 142, 35),
('Lebanon', 'LB', 'LBN', 422, 'LBN', 'Asia', 'Western Asia', 142, 145),
('Lesotho', 'LS', 'LSO', 426, 'LES', 'Africa', 'Southern Africa', 2, 18),
('Latvia', 'LV', 'LVA', 428, 'LAT', 'Europe', 'Northern Europe', 150, 154),
('Liberia', 'LR', 'LBR', 430, 'LBR', 'Africa', 'Western Africa', 2, 11),
('Libya', 'LY', 'LBY', 434, 'LBA', 'Africa', 'Northern Africa', 2, 15),
('Liechtenstein', 'LI', 'LIE', 438, 'LIE', 'Europe', 'Western Europe', 150, 155),
('Lithuania', 'LT', 'LTU', 440, 'LTU', 'Europe', 'Northern Europe', 150, 154),
('Luxembourg', 'LU', 'LUX', 442, 'LUX', 'Europe', 'Western Europe', 150, 155),
('Macao', 'MO', 'MAC', 446, NULL, 'Asia', 'Eastern Asia', 142, 30),
('Madagascar', 'MG', 'MDG', 450, 'MAD', 'Africa', 'Eastern Africa', 2, 14),
('Malawi', 'MW', 'MWI', 454, 'MAW', 'Africa', 'Eastern Africa', 2, 14),
('Malaysia', 'MY', 'MYS', 458, 'MAS', 'Asia', 'South-Eastern Asia', 142, 35),
('Maldives', 'MV', 'MDV', 462, 'MDV', 'Asia', 'Southern Asia', 142, 34),
('Mali', 'ML', 'MLI', 466, 'MLI', 'Africa', 'Western Africa', 2, 11),
('Malta', 'MT', 'MLT', 470, 'MLT', 'Europe', 'Southern Europe', 150, 39),
('Martinique', 'MQ', 'MTQ', 474, NULL, 'Americas', 'Caribbean', 19, 29),
('Mauritania', 'MR', 'MRT', 478, 'MTN', 'Africa', 'Western Africa', 2, 11),
('Mauritius', 'MU', 'MUS', 480, 'MRI', 'Africa', 'Eastern Africa', 2, 14),
('Mexico', 'MX', 'MEX', 484, 'MEX', 'Americas', 'Central America', 19, 13),
('Monaco', 'MC', 'MCO', 492, 'MON', 'Europe', 'Western Europe', 150, 155),
('Mongolia', 'MN', 'MNG', 496, 'MGL', 'Asia', 'Eastern Asia', 142, 30),
('Moldova', 'MD', 'MDA', 498, 'MDA', 'Europe', 'Eastern Europe', 150, 151),
('Montenegro', 'ME', 'MNE', 499, 'MNE', 'Europe', 'Southern Europe', 150, 39),
('Montserrat', 'MS', 'MSR', 500, NULL, 'Americas', 'Caribbean', 19, 29),
('Morocco', 'MA', 'MAR', 504, 'MAR', 'Africa', 'Northern Africa', 2, 15),
('Mozambique', 'MZ', 'MOZ', 508, 'MOZ', 'Africa', 'Eastern Africa', 2, 14),
('Oman', 'OM', 'OMN', 512, 'OMA', 'Asia', 'Western Asia', 142, 145),
('Namibia', 'NA', 'NAM', 516, 'NAM', 'Africa', 'Southern Africa', 2, 18),
('Nauru', 'NR', 'NRU', 520, 'NRU', 'Oceania', 'Micronesia', 9, 57),
('Nepal', 'NP', 'NPL', 524, 'NEP', 'Asia', 'Southern Asia', 142, 34),
('Netherlands', 'NL', 'NLD', 528, 'NED', 'Europe', 'Western Europe', 150, 155),
('Curacao', 'CW', 'CUW', 531, NULL, 'Americas', 'Caribbean', 19, 29),
('Aruba', 'AW', 'ABW', 533, 'ARU', 'Americas', 'Caribbean', 19, 29),
('Sint Maarten', 'SX', 'SXM', 534, NULL, 'Americas', 'Caribbean', 19, 29),
('Bonaire, Saint Eustatius and Saba', 'BQ', 'BES', 535, NULL, 'Americas', 'Caribbean', 19, 29),
('New Caledonia', 'NC', 'NCL', 540, NULL, 'Oceania', 'Melanesia', 9, 54),
('Vanuatu', 'VU', 'VUT', 548, 'VAN', 'Oceania', 'Melanesia', 9, 54),
('New Zealand', 'NZ', 'NZL', 554, 'NZL', 'Oceania', 'Australia and New Zealand', 9, 53),
('Nicaragua', 'NI', 'NIC', 558, 'NCA', 'Americas', 'Central America', 19, 13),
('Niger', 'NE', 'NER', 562, 'NIG', 'Africa', 'Western Africa', 2, 11),
('Nigeria', 'NG', 'NGA', 566, 'NGR', 'Africa', 'Western Africa', 2, 11),
('Niue', 'NU', 'NIU', 570, NULL, 'Oceania', 'Polynesia', 9, 61),
('Norfolk Island', 'NF', 'NFK', 574, NULL, 'Oceania', 'Australia and New Zealand', 9, 53),
('Norway', 'NO', 'NOR', 578, 'NOR', 'Europe', 'Northern Europe', 150, 154),
('Northern Mariana Islands', 'MP', 'MNP', 580, NULL, 'Oceania', 'Micronesia', 9, 57),
('United States Minor Outlying Islands', 'UM', 'UMI', 581, NULL, NULL, NULL, NULL, NULL),
('Federated States of Micronesia', 'FM', 'FSM', 583, 'FSM', 'Oceania', 'Micronesia', 9, 57),
('Marshall Islands', 'MH', 'MHL', 584, 'MHL', 'Oceania', 'Micronesia', 9, 57),
('Palau', 'PW', 'PLW', 585, 'PLW', 'Oceania', 'Micronesia', 9, 57),
('Pakistan', 'PK', 'PAK', 586, 'PAK', 'Asia', 'Southern Asia', 142, 34),
('Panama', 'PA', 'PAN', 591, 'PAN', 'Americas', 'Central America', 19, 13),
('Papua New Guinea', 'PG', 'PNG', 598, 'PNG', 'Oceania', 'Melanesia', 9, 54),
('Paraguay', 'PY', 'PRY', 600, 'PAR', 'Americas', 'South America', 19, 5),
('Peru', 'PE', 'PER', 604, 'PER', 'Americas', 'South America', 19, 5),
('Philippines', 'PH', 'PHL', 608, 'PHI', 'Asia', 'South-Eastern Asia', 142, 35),
('Pitcairn Islands', 'PN', 'PCN', 612, NULL, 'Oceania', 'Polynesia', 9, 61),
('Poland', 'PL', 'POL', 616, 'POL', 'Europe', 'Eastern Europe', 150, 151),
('Portugal', 'PT', 'PRT', 620, 'POR', 'Europe', 'Southern Europe', 150, 39),
('Guinea-Bissau', 'GW', 'GNB', 624, 'GBS', 'Africa', 'Western Africa', 2, 11),
('East Timor', 'TL', 'TLS', 626, 'TLS', 'Asia', 'South-Eastern Asia', 142, 35),
('Puerto Rico', 'PR', 'PRI', 630, 'PUR', 'Americas', 'Caribbean', 19, 29),
('Qatar', 'QA', 'QAT', 634, 'QAT', 'Asia', 'Western Asia', 142, 145),
('Reunion', 'RE', 'REU', 638, NULL, 'Africa', 'Eastern Africa', 2, 14),
('Romania', 'RO', 'ROU', 642, 'ROU', 'Europe', 'Eastern Europe', 150, 151),
('Russia', 'RU', 'RUS', 643, 'RUS', 'Europe', 'Eastern Europe', 150, 151),
('Rwanda', 'RW', 'RWA', 646, 'RWA', 'Africa', 'Eastern Africa', 2, 14),
('Saint Barthelemy', 'BL', 'BLM', 652, NULL, 'Americas', 'Caribbean', 19, 29),
('Saint Helena, Ascension and Tristan da Cunha', 'SH', 'SHN', 654, NULL, 'Africa', 'Western Africa', 2, 11),
('Saint Kitts and Nevis', 'KN', 'KNA', 659, 'SKN', 'Americas', 'Caribbean', 19, 29),
('Anguilla', 'AI', 'AIA', 660, NULL, 'Americas', 'Caribbean', 19, 29),
('Saint Lucia', 'LC', 'LCA', 662, 'LCA', 'Americas', 'Caribbean', 19, 29),
('Saint Martin', 'MF', 'MAF', 663, NULL, 'Americas', 'Caribbean', 19, 29),
('Saint Pierre and Miquelon', 'PM', 'SPM', 666, NULL, 'Americas', 'Northern America', 19, 21),
('Saint Vincent and the Grenadines', 'VC', 'VCT', 670, 'VIN', 'Americas', 'Caribbean', 19, 29),
('San Marino', 'SM', 'SMR', 674, 'SMR', 'Europe', 'Southern Europe', 150, 39),
('Sao Tome and Principe', 'ST', 'STP', 678, 'STP', 'Africa', 'Middle Africa', 2, 17),
('Saudi Arabia', 'SA', 'SAU', 682, 'KSA', 'Asia', 'Western Asia', 142, 145),
('Senegal', 'SN', 'SEN', 686, 'SEN', 'Africa', 'Western Africa', 2, 11),
('Serbia', 'RS', 'SRB', 688, 'SRB', 'Europe', 'Southern Europe', 150, 39),
('Seychelles', 'SC', 'SYC', 690, 'SEY', 'Africa', 'Eastern Africa', 2, 14),
('Sierra Leone', 'SL', 'SLE', 694, 'SLE', 'Africa', 'Western Africa', 2, 11),
('Singapore', 'SG', 'SGP', 702, 'SGP', 'Asia', 'South-Eastern Asia', 142, 35),
('Slovakia', 'SK', 'SVK', 703, 'SVK', 'Europe', 'Eastern Europe', 150, 151),
('Vietnam', 'VN', 'VNM', 704, 'VIE', 'Asia', 'South-Eastern Asia', 142, 35),
('Slovenia', 'SI', 'SVN', 705, 'SLO', 'Europe', 'Southern Europe', 150, 39),
('Somalia', 'SO', 'SOM', 706, 'SOM', 'Africa', 'Eastern Africa', 2, 14),
('South Africa', 'ZA', 'ZAF', 710, 'RSA', 'Africa', 'Southern Africa', 2, 18),
('Zimbabwe', 'ZW', 'ZWE', 716, 'ZIM', 'Africa', 'Eastern Africa', 2, 14),
('Spain', 'ES', 'ESP', 724, 'ESP', 'Europe', 'Southern Europe', 150, 39),
('South Sudan', 'SS', 'SSD', 728, NULL, 'Africa', 'Eastern Africa', 2, 14),
('Sudan', 'SD', 'SDN', 729, 'SUD', 'Africa', 'Northern Africa', 2, 15),
('Western Sahara', 'EH', 'ESH', 732, NULL, 'Africa', 'Northern Africa', 2, 15),
('Suriname', 'SR', 'SUR', 740, 'SUR', 'Americas', 'South America', 19, 5),
('Svalbard', 'SJ', 'SJM', 744, NULL, 'Europe', 'Northern Europe', 150, 154),
('Swaziland', 'SZ', 'SWZ', 748, 'SWZ', 'Africa', 'Southern Africa', 2, 18),
('Sweden', 'SE', 'SWE', 752, 'SWE', 'Europe', 'Northern Europe', 150, 154),
('Switzerland', 'CH', 'CHE', 756, 'SUI', 'Europe', 'Western Europe', 150, 155),
('Syria', 'SY', 'SYR', 760, 'SYR', 'Asia', 'Western Asia', 142, 145),
('Tajikistan', 'TJ', 'TJK', 762, 'TJK', 'Asia', 'Central Asia', 142, 143),
('Thailand', 'TH', 'THA', 764, 'THA', 'Asia', 'South-Eastern Asia', 142, 35),
('Togo', 'TG', 'TGO', 768, 'TOG', 'Africa', 'Western Africa', 2, 11),
('Tokelau', 'TK', 'TKL', 772, NULL, 'Oceania', 'Polynesia', 9, 61),
('Tonga', 'TO', 'TON', 776, 'TGA', 'Oceania', 'Polynesia', 9, 61),
('Trinidad and Tobago', 'TT', 'TTO', 780, 'TTO', 'Americas', 'Caribbean', 19, 29),
('United Arab Emirates', 'AE', 'ARE', 784, 'UAE', 'Asia', 'Western Asia', 142, 145),
('Tunisia', 'TN', 'TUN', 788, 'TUN', 'Africa', 'Northern Africa', 2, 15),
('Turkey', 'TR', 'TUR', 792, 'TUR', 'Asia', 'Western Asia', 142, 145),
('Turkmenistan', 'TM', 'TKM', 795, 'TKM', 'Asia', 'Central Asia', 142, 143),
('Turks and Caicos Islands', 'TC', 'TCA', 796, NULL, 'Americas', 'Caribbean', 19, 29),
('Tuvalu', 'TV', 'TUV', 798, 'TUV', 'Oceania', 'Polynesia', 9, 61),
('Uganda', 'UG', 'UGA', 800, 'UGA', 'Africa', 'Eastern Africa', 2, 14),
('Ukraine', 'UA', 'UKR', 804, 'UKR', 'Europe', 'Eastern Europe', 150, 151),
('North Macedonia', 'MK', 'MKD', 807, 'MKD', 'Europe', 'Southern Europe', 150, 39),
('Egypt', 'EG', 'EGY', 818, 'EGY', 'Africa', 'Northern Africa', 2, 15),
('United Kingdom', 'GB', 'GBR', 826, 'GBR', 'Europe', 'Northern Europe', 150, 154),
('Guernsey', 'GG', 'GGY', 831, NULL, 'Europe', 'Northern Europe', 150, 154),
('Jersey', 'JE', 'JEY', 832, NULL, 'Europe', 'Northern Europe', 150, 154),
('Isle of Man', 'IM', 'IMN', 833, NULL, 'Europe', 'Northern Europe', 150, 154),
('Tanzania', 'TZ', 'TZA', 834, 'TAN', 'Africa', 'Eastern Africa', 2, 14),
('United States', 'US', 'USA', 840, 'USA', 'Americas', 'Northern America', 19, 21),
('Virgin Islands', 'VI', 'VIR', 850, 'ISV', 'Americas', 'Caribbean', 19, 29),
('Burkina Faso', 'BF', 'BFA', 854, 'BUR', 'Africa', 'Western Africa', 2, 11),
('Uruguay', 'UY', 'URY', 858, 'URU', 'Americas', 'South America', 19, 5),
('Uzbekistan', 'UZ', 'UZB', 860, 'UZB', 'Asia', 'Central Asia', 142, 143),
('Venezuela', 'VE', 'VEN', 862, 'VEN', 'Americas', 'South America', 19, 5),
('Wallis and Futuna', 'WF', 'WLF', 876, NULL, 'Oceania', 'Polynesia', 9, 61),
('Samoa', 'WS', 'WSM', 882, 'SAM', 'Oceania', 'Polynesia', 9, 61),
('Yemen', 'YE', 'YEM', 887, 'YEM', 'Asia', 'Western Asia', 142, 145),
('Zambia', 'ZM', 'ZMB', 894, 'ZAM', 'Africa', 'Eastern Africa', 2, 14),
('Kosovo', 'XK', 'XKX', 999, 'KOS', 'Europe', 'Southern Europe', 150, 39);

--
-- Indexes for dumped tables
--


--
-- Table structure for table `tblLadderComp`
--

CREATE TABLE `tblLadderComp` (
  `ladder_id` int(11) DEFAULT NULL,
  `comp_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `tblLadderSeason`
--

CREATE TABLE `tblLadderSeason` (
  `ladder_id` int(11) NOT NULL,
  `season` int(6) NOT NULL,
  `active` tinyint(1) DEFAULT '1',
  `overall_validity` enum('all','ftv','round') NOT NULL DEFAULT 'ftv',
  `validity_param` decimal(4,3) NOT NULL DEFAULT '0.750'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `tblNotification`
--

CREATE TABLE `tblNotification` (
  `not_id` int(11) NOT NULL,
  `track_id` int(11) NOT NULL,
  `notification_type` enum('custom','track','jtg','auto') NOT NULL DEFAULT 'custom',
  `flat_penalty` decimal(8,4) NOT NULL DEFAULT '0.0000',
  `percentage_penalty` decimal(5,4) NOT NULL DEFAULT '0.0000',
  `comment` varchar(80) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

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
  `name` varchar(100) DEFAULT NULL,
  `birthdate` date DEFAULT NULL,
  `sex` enum('M','F') NOT NULL DEFAULT 'M',
  `nat` char(10) DEFAULT NULL,
  `glider` varchar(100) DEFAULT NULL,
  `glider_cert` varchar(20) DEFAULT NULL,
  `sponsor` varchar(500) DEFAULT NULL,
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `tblParticipantMeta`
--

CREATE TABLE `tblParticipantMeta` (
  `pat_id` int NOT NULL,
  `par_id` int NOT NULL,
  `attr_id` int NOT NULL,
  `meta_value` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `tblRegionWaypoint`
--

CREATE TABLE `tblRegionWaypoint` (
  `rwp_id` int(11) NOT NULL,
  `reg_id` int(11) DEFAULT NULL,
  `name` varchar(12) NOT NULL,
  `lat` decimal(8,6) NOT NULL,
  `lon` decimal(9,6) NOT NULL,
  `altitude` smallint(6) NOT NULL,
  `description` varchar(64) DEFAULT NULL,
  `old` tinyint(1) NOT NULL DEFAULT '0',
  `xccSiteID` int(11) DEFAULT NULL,
  `xccToID` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `tblRegionXCSites`
--

CREATE TABLE `tblRegionXCSites` (
  `reg_id` int(11) NOT NULL,
  `xccSiteID` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `tblTask`
--

CREATE TABLE `tblTask` (
  `task_id` int(11) NOT NULL,
  `comp_id` int(11) DEFAULT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `task_num` tinyint(4) NOT NULL,
  `task_name` varchar(100) DEFAULT NULL,
  `training` tinyint(1) NOT NULL DEFAULT '0',
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
  `no_goal_penalty` decimal(4,3) DEFAULT NULL,
  `tolerance` decimal(6,5) DEFAULT NULL,
  `airspace_check` tinyint(1) DEFAULT NULL,
  `openair_file` varchar(40) DEFAULT NULL,
  `QNH` decimal(7,3) NOT NULL DEFAULT '1013.250',
  `comment` text,
  `locked` tinyint(3) NOT NULL DEFAULT '0',
  `task_path` varchar(40) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `tblTaskResult`
--

CREATE TABLE `tblTaskResult` (
  `track_id` int(11) NOT NULL,
  `task_id` int(11) DEFAULT NULL,
  `par_id` int(11) DEFAULT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `track_file` varchar(255) DEFAULT NULL,
  `g_record` tinyint(4) DEFAULT '1',
  `best_dist_to_ESS` double DEFAULT NULL,
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `tblTaskWaypoint`
--

CREATE TABLE `tblTaskWaypoint` (
  `wpt_id` int(11) NOT NULL,
  `task_id` int(11) DEFAULT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `num` tinyint(4) NOT NULL,
  `name` varchar(12) NOT NULL,
  `rwp_id` int(11) DEFAULT NULL,
  `lat` decimal(8,6) NOT NULL,
  `lon` decimal(9,6) NOT NULL,
  `altitude` smallint(6) NOT NULL DEFAULT '0',
  `description` varchar(64) DEFAULT NULL,
  `time` mediumint(9) DEFAULT NULL,
  `type` enum('waypoint','launch','speed','endspeed','goal') DEFAULT 'waypoint',
  `how` enum('entry','exit') DEFAULT 'entry',
  `shape` enum('circle','semicircle','line') DEFAULT 'circle',
  `angle` smallint(6) DEFAULT NULL,
  `radius` mediumint(9) DEFAULT NULL,
  `ssr_lat` decimal(8,6) DEFAULT NULL,
  `ssr_lon` decimal(9,6) DEFAULT NULL,
  `partial_distance` double DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

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
  `lat` decimal(8,6) NOT NULL,
  `lon` decimal(9,6) NOT NULL,
  `altitude` smallint(6) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

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
,`sponsor` varchar(500)
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
  `access` enum('pilot','scorekeeper','manager','admin','pending') NOT NULL DEFAULT 'pilot'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Structure for view `CompObjectView`
--
DROP TABLE IF EXISTS `CompObjectView`;

CREATE ALGORITHM=UNDEFINED DEFINER=CURRENT_USER SQL SECURITY DEFINER VIEW `CompObjectView`  AS  select `C`.`comp_id` AS `comp_id`,`C`.`comp_name` AS `comp_name`,`C`.`comp_site` AS `comp_site`,`C`.`date_from` AS `date_from`,`C`.`date_to` AS `date_to`,`C`.`MD_name` AS `MD_name`,`C`.`contact` AS `contact`,`C`.`sanction` AS `sanction`,`C`.`comp_type` AS `comp_type`,`C`.`comp_code` AS `comp_code`,`C`.`restricted` AS `restricted`,`C`.`time_offset` AS `time_offset`,`C`.`comp_class` AS `comp_class`,`C`.`openair_file` AS `openair_file`,`C`.`stylesheet` AS `stylesheet`,`C`.`locked` AS `locked`,`C`.`comp_path` AS `comp_path`,`C`.`external` AS `external`,`C`.`website` AS `website`,`C`.`airspace_check` AS `airspace_check`,`C`.`check_launch` AS `check_launch`,`C`.`igc_config_file` AS `igc_config_file`,`C`.`self_register` AS `self_register`,`C`.`check_g_record` AS `check_g_record`,`C`.`track_source` AS `track_source`,`FC`.`formula_name` AS `formula_name`,`FC`.`overall_validity` AS `overall_validity`,`FC`.`validity_param` AS `validity_param`,`FC`.`validity_ref` AS `validity_ref`,`FC`.`nominal_goal` AS `nominal_goal`,`FC`.`min_dist` AS `min_dist`,`FC`.`nominal_dist` AS `nominal_dist`,`FC`.`nominal_time` AS `nominal_time`,`FC`.`nominal_launch` AS `nominal_launch`,`FC`.`formula_distance` AS `formula_distance`,`FC`.`formula_arrival` AS `formula_arrival`,`FC`.`formula_departure` AS `formula_departure`,`FC`.`lead_factor` AS `lead_factor`,`FC`.`formula_time` AS `formula_time`,`FC`.`no_goal_penalty` AS `no_goal_penalty`,`FC`.`glide_bonus` AS `glide_bonus`,`FC`.`tolerance` AS `tolerance`,`FC`.`min_tolerance` AS `min_tolerance`,`FC`.`arr_alt_bonus` AS `arr_alt_bonus`,`FC`.`arr_min_height` AS `arr_min_height`,`FC`.`arr_max_height` AS `arr_max_height`,`FC`.`validity_min_time` AS `validity_min_time`,`FC`.`score_back_time` AS `score_back_time`,`FC`.`max_JTG` AS `max_JTG`,`FC`.`JTG_penalty_per_sec` AS `JTG_penalty_per_sec`,`FC`.`scoring_altitude` AS `scoring_altitude`,`FC`.`task_result_decimal` AS `task_result_decimal`,`FC`.`comp_result_decimal` AS `comp_result_decimal`,`FC`.`team_scoring` AS `team_scoring`,`FC`.`team_size` AS `team_size`,`FC`.`max_team_size` AS `max_team_size`,`FC`.`country_scoring` AS `country_scoring`,`FC`.`country_size` AS `country_size`,`FC`.`max_country_size` AS `max_country_size`,`FC`.`team_over` AS `team_over` from (`tblCompetition` `C` left join `tblForComp` `FC` on((`C`.`comp_id` = `FC`.`comp_id`))) order by (case when (`C`.`comp_name` like '%test%') then `C`.`comp_name` else `C`.`date_to` end) desc ;

-- --------------------------------------------------------

--
-- Structure for view `FlightResultView`
--
DROP TABLE IF EXISTS `FlightResultView`;

CREATE ALGORITHM=UNDEFINED DEFINER=CURRENT_USER SQL SECURITY DEFINER VIEW `FlightResultView`  AS  select `T`.`track_id` AS `track_id`,`T`.`par_id` AS `par_id`,`T`.`task_id` AS `task_id`,`R`.`comp_id` AS `comp_id`,`R`.`civl_id` AS `civl_id`,`R`.`fai_id` AS `fai_id`,`R`.`pil_id` AS `pil_id`,`R`.`ID` AS `ID`,`R`.`name` AS `name`,`R`.`nat` AS `nat`,`R`.`sex` AS `sex`,`R`.`glider` AS `glider`,`R`.`glider_cert` AS `glider_cert`,`R`.`sponsor` AS `sponsor`,`R`.`team` AS `team`,`R`.`nat_team` AS `nat_team`,`R`.`live_id` AS `live_id`,`T`.`distance_flown` AS `distance_flown`,`T`.`best_dist_to_ESS` AS `best_dist_to_ESS`,`T`.`best_distance_time` AS `best_distance_time`,`T`.`stopped_distance` AS `stopped_distance`,`T`.`stopped_altitude` AS `stopped_altitude`,`T`.`total_distance` AS `total_distance`,`T`.`speed` AS `speed`,`T`.`first_time` AS `first_time`,`T`.`real_start_time` AS `real_start_time`,`T`.`goal_time` AS `goal_time`,`T`.`last_time` AS `last_time`,`T`.`result_type` AS `result_type`,`T`.`SSS_time` AS `SSS_time`,`T`.`ESS_time` AS `ESS_time`,`T`.`waypoints_made` AS `waypoints_made`,`T`.`penalty` AS `penalty`,`T`.`comment` AS `comment`,`T`.`time_score` AS `time_score`,`T`.`distance_score` AS `distance_score`,`T`.`arrival_score` AS `arrival_score`,`T`.`departure_score` AS `departure_score`,`T`.`score` AS `score`,`T`.`lead_coeff` AS `lead_coeff`,`T`.`fixed_LC` AS `fixed_LC`,`T`.`ESS_altitude` AS `ESS_altitude`,`T`.`goal_altitude` AS `goal_altitude`,`T`.`max_altitude` AS `max_altitude`,`T`.`last_altitude` AS `last_altitude`,`T`.`landing_altitude` AS `landing_altitude`,`T`.`landing_time` AS `landing_time`,`T`.`track_file` AS `track_file`,`T`.`g_record` AS `g_record` from (`tblTaskResult` `T` join `tblParticipant` `R` on((`T`.`par_id` = `R`.`par_id`))) order by `T`.`task_id`,`T`.`score` desc ;

-- --------------------------------------------------------

--
-- Structure for view `RegionWaypointView`
--
DROP TABLE IF EXISTS `RegionWaypointView`;

CREATE ALGORITHM=UNDEFINED DEFINER=CURRENT_USER SQL SECURITY DEFINER VIEW `RegionWaypointView`  AS  select `tblRegionWaypoint`.`rwp_id` AS `rwp_id`,`tblRegionWaypoint`.`reg_id` AS `region_id`,`tblRegionWaypoint`.`name` AS `name`,`tblRegionWaypoint`.`lat` AS `lat`,`tblRegionWaypoint`.`lon` AS `lon`,`tblRegionWaypoint`.`altitude` AS `altitude`,`tblRegionWaypoint`.`description` AS `description` from `tblRegionWaypoint` where (`tblRegionWaypoint`.`old` = 0) ;

-- --------------------------------------------------------

--
-- Structure for view `TaskFormulaView`
--
DROP TABLE IF EXISTS `TaskFormulaView`;

CREATE ALGORITHM=UNDEFINED DEFINER=CURRENT_USER SQL SECURITY DEFINER VIEW `TaskFormulaView`  AS  select `FC`.`comp_id` AS `comp_id`,`T`.`task_id` AS `task_id`,`FC`.`formula_name` AS `formula_name`,`C`.`comp_class` AS `comp_class`,`FC`.`overall_validity` AS `overall_validity`,`FC`.`validity_param` AS `validity_param`,`FC`.`validity_ref` AS `validity_ref`,`FC`.`nominal_goal` AS `nominal_goal`,`FC`.`min_dist` AS `min_dist`,`FC`.`nominal_dist` AS `nominal_dist`,`FC`.`nominal_time` AS `nominal_time`,`FC`.`nominal_launch` AS `nominal_launch`,`T`.`formula_distance` AS `formula_distance`,`T`.`formula_departure` AS `formula_departure`,`T`.`formula_arrival` AS `formula_arrival`,`T`.`formula_time` AS `formula_time`,`FC`.`lead_factor` AS `lead_factor`,`T`.`no_goal_penalty` AS `no_goal_penalty`,`FC`.`glide_bonus` AS `glide_bonus`,`T`.`tolerance` AS `tolerance`,`FC`.`min_tolerance` AS `min_tolerance`,`T`.`arr_alt_bonus` AS `arr_alt_bonus`,`FC`.`arr_min_height` AS `arr_min_height`,`FC`.`arr_max_height` AS `arr_max_height`,`FC`.`validity_min_time` AS `validity_min_time`,`FC`.`score_back_time` AS `score_back_time`,`T`.`max_JTG` AS `max_JTG`,`FC`.`JTG_penalty_per_sec` AS `JTG_penalty_per_sec`,`FC`.`scoring_altitude` AS `scoring_altitude`,`FC`.`task_result_decimal` AS `task_result_decimal`,`FC`.`team_scoring` AS `team_scoring`,`FC`.`team_size` AS `team_size`,`FC`.`max_team_size` AS `max_team_size`,`FC`.`country_scoring` AS `country_scoring`,`FC`.`country_size` AS `country_size`,`FC`.`max_country_size` AS `max_country_size` from (`tblTask` `T` join `tblForComp` `FC` on((`T`.`comp_id` = `FC`.`comp_id`)) join `tblCompetition` `C` on((`T`.`comp_id` = `C`.`comp_id`))) order by `T`.`task_id` ;

-- --------------------------------------------------------

--
-- Structure for view `TaskObjectView`
--
DROP TABLE IF EXISTS `TaskObjectView`;

CREATE ALGORITHM=UNDEFINED DEFINER=CURRENT_USER SQL SECURITY DEFINER VIEW `TaskObjectView`  AS  select `T`.`task_id` AS `task_id`,`C`.`comp_code` AS `comp_code`,`C`.`comp_name` AS `comp_name`,`C`.`comp_site` AS `comp_site`,`T`.`time_offset` AS `time_offset`,`C`.`comp_class` AS `comp_class`,`T`.`comp_id` AS `comp_id`,`T`.`date` AS `date`,`T`.`task_name` AS `task_name`,`T`.`task_num` AS `task_num`,`T`.`reg_id` AS `reg_id`,`T`.`training` AS `training`,`R`.`description` AS `region_name`,`T`.`window_open_time` AS `window_open_time`,`T`.`task_deadline` AS `task_deadline`,`T`.`window_close_time` AS `window_close_time`,`T`.`check_launch` AS `check_launch`,`T`.`start_time` AS `start_time`,`T`.`SS_interval` AS `SS_interval`,`T`.`start_iteration` AS `start_iteration`,`T`.`start_close_time` AS `start_close_time`,`T`.`stopped_time` AS `stopped_time`,`T`.`task_type` AS `task_type`,`T`.`distance` AS `distance`,`T`.`opt_dist` AS `opt_dist`,`T`.`opt_dist_to_SS` AS `opt_dist_to_SS`,`T`.`opt_dist_to_ESS` AS `opt_dist_to_ESS`,`T`.`SS_distance` AS `SS_distance`,`T`.`QNH` AS `QNH`,`T`.`comment` AS `comment`,`T`.`locked` AS `locked`,`T`.`airspace_check` AS `airspace_check`,`T`.`openair_file` AS `openair_file`,`T`.`cancelled` AS `cancelled`,`C`.`track_source` AS `track_source`,`T`.`task_path` AS `task_path`,`C`.`comp_path` AS `comp_path`,`C`.`igc_config_file` AS `igc_config_file` from ((`tblTask` `T` join `tblCompetition` `C` on((`T`.`comp_id` = `C`.`comp_id`))) left join `tblRegion` `R` on((`T`.`reg_id` = `R`.`reg_id`))) order by `T`.`date` ;

-- --------------------------------------------------------

--
-- Structure for view `TrackObjectView`
--
DROP TABLE IF EXISTS `TrackObjectView`;

CREATE ALGORITHM=UNDEFINED DEFINER=CURRENT_USER SQL SECURITY DEFINER VIEW `TrackObjectView`  AS  select `T`.`track_id` AS `track_id`,`T`.`par_id` AS `par_id`,`T`.`task_id` AS `task_id`,`R`.`civl_id` AS `civl_id`,`R`.`glider` AS `glider`,`R`.`glider_cert` AS `glider_cert`,`T`.`track_file` AS `track_file` from (`tblTaskResult` `T` join `tblParticipant` `R` on((`T`.`par_id` = `R`.`par_id`))) where (`T`.`track_file` is not null) order by `T`.`track_id` ;

-- --------------------------------------------------------

--
-- Structure for view `UnscoredPilotView`
--
DROP TABLE IF EXISTS `UnscoredPilotView`;

CREATE ALGORITHM=UNDEFINED DEFINER=CURRENT_USER SQL SECURITY DEFINER VIEW `UnscoredPilotView`  AS  select `T`.`task_id` AS `task_id`,`R`.`par_id` AS `par_id`,`R`.`comp_id` AS `comp_id`,`R`.`civl_id` AS `civl_id`,`R`.`fai_id` AS `fai_id`,`R`.`pil_id` AS `pil_id`,`R`.`ID` AS `ID`,`R`.`name` AS `name`,`R`.`sex` AS `sex`,`R`.`nat` AS `nat`,`R`.`glider` AS `glider`,`R`.`glider_cert` AS `glider_cert`,`R`.`sponsor` AS `sponsor`,`R`.`xcontest_id` AS `xcontest_id`,`R`.`live_id` AS `live_id`,`R`.`team` AS `team`,`R`.`nat_team` AS `nat_team` from ((`tblParticipant` `R` join `tblTask` `T` on((`R`.`comp_id` = `T`.`comp_id`))) left join `tblTaskResult` `TR` on(((`T`.`task_id` = `TR`.`task_id`) and (`R`.`par_id` = `TR`.`par_id`)))) where isnull(`TR`.`track_id`) order by `T`.`task_id`,`R`.`par_id` ;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `tblCertification`
--
ALTER TABLE `tblCertification`
  ADD PRIMARY KEY (`cert_id`);

--
-- Indexes for table `tblAirspaceCheck`
--
ALTER TABLE `tblAirspaceCheck`
  ADD PRIMARY KEY (`check_id`),
  ADD KEY `comp_id` (`comp_id`),
  ADD KEY `task_id` (`task_id`);

--
-- Indexes for table `tblCompetition`
--
ALTER TABLE `tblCompetition`
  ADD PRIMARY KEY (`comp_id`) USING BTREE,
  ADD UNIQUE KEY `comp_id` (`comp_id`,`comp_name`);

--
-- Indexes for table `tblCompAttribute`
--
ALTER TABLE `tblCompAttribute`
  ADD PRIMARY KEY (`attr_id`),
  ADD KEY `comp_id` (`comp_id`);

--
-- Indexes for table `tblCompRanking`
--
ALTER TABLE `tblCompRanking`
  ADD PRIMARY KEY (`rank_id`),
  ADD KEY `comp_id` (`comp_id`),
  ADD KEY `attr_id` (`attr_id`),
  ADD KEY `cert_id` (`cert_id`);

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
-- Indexes for table `tblLadder`
--
ALTER TABLE `tblLadderRanking`
  ADD PRIMARY KEY (`rank_id`),
  ADD KEY `cert_id` (`cert_id`),
  ADD KEY `ladder_id` (`ladder_id`);

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
-- Indexes for table `tblParticipantMeta`
--
ALTER TABLE `tblParticipantMeta`
  ADD PRIMARY KEY (`pat_id`),
  ADD KEY `par_id` (`par_id`),
  ADD KEY `attr_id` (`attr_id`);

--
-- Indexes for table `tblCountryCode`
--
ALTER TABLE `tblCountryCode`
  ADD PRIMARY KEY (`natId`);

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
-- AUTO_INCREMENT for table `tblCompetition`
--
ALTER TABLE `tblAirspaceCheck`
  MODIFY `check_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `tblCompetition`
--
ALTER TABLE `tblCompetition`
  MODIFY `comp_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `tblCompAttribute`
--
ALTER TABLE `tblCompAttribute`
  MODIFY `attr_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `tblCompRanking`
--
ALTER TABLE `tblCompRanking`
  MODIFY `rank_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `tblLadder`
--
ALTER TABLE `tblLadder`
  MODIFY `ladder_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `tblLadderRanking`
--
ALTER TABLE `tblLadderRanking`
  MODIFY `rank_id` int(11) NOT NULL AUTO_INCREMENT;

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
-- AUTO_INCREMENT for table `tblParticipantMeta`
--
ALTER TABLE `tblParticipantMeta`
  MODIFY `pat_id` int(11) NOT NULL AUTO_INCREMENT;

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


--
-- CONSTRAINS
--

--
-- Constraints for table `tblAirspaceCheck`
--
ALTER TABLE `tblAirspaceCheck`
  ADD CONSTRAINT `tblAirspaceCheck_ibfk_2` FOREIGN KEY (`comp_id`) REFERENCES `tblCompetition` (`comp_id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  ADD CONSTRAINT `tblAirspaceCheck_ibfk_3` FOREIGN KEY (`task_id`) REFERENCES `tblTask` (`task_id`) ON DELETE CASCADE ON UPDATE RESTRICT;

--
-- Constraints for table `tblCompAttribute`
--
ALTER TABLE `tblCompAttribute`
  ADD CONSTRAINT `tblCompAttribute_ibfk_2` FOREIGN KEY (`comp_id`) REFERENCES `tblCompetition` (`comp_id`) ON DELETE CASCADE ON UPDATE RESTRICT;

--
-- Constraints for table `tblCompRanking`
--
ALTER TABLE `tblCompRanking`
  ADD CONSTRAINT `tblCompRanking_ibfk_4` FOREIGN KEY (`comp_id`) REFERENCES `tblCompetition` (`comp_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `tblCompRanking_ibfk_6` FOREIGN KEY (`attr_id`) REFERENCES `tblCompAttribute` (`attr_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `tblCompRanking_ibfk_7` FOREIGN KEY (`cert_id`) REFERENCES `tblCertification` (`cert_id`);

--
-- Indexes for table `tblLadder`
--
ALTER TABLE `tblLadderRanking`
  ADD CONSTRAINT `tblLadderRanking_ibfk_2` FOREIGN KEY (`cert_id`) REFERENCES `tblCertification` (`cert_id`),
  ADD CONSTRAINT `tblLadderRanking_ibfk_3` FOREIGN KEY (`ladder_id`) REFERENCES `tblLadder` (`ladder_id`) ON DELETE CASCADE ON UPDATE RESTRICT;

--
-- Indexes for table `tblParticipantMeta`
--
ALTER TABLE `tblParticipantMeta`
  ADD CONSTRAINT `tblParticipantMeta_ibfk_3` FOREIGN KEY (`par_id`) REFERENCES `tblParticipant` (`par_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `tblParticipantMeta_ibfk_4` FOREIGN KEY (`attr_id`) REFERENCES `tblCompAttribute` (`attr_id`) ON DELETE CASCADE;

COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
