USE airscore

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
,`track_source` varchar(40)
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

--
-- Dumping data for table `tblCountryCode`
--

INSERT INTO `tblCountryCode` (`natName`, `natIso2`, `natIso3`, `natId`, `natIso`, `natRegion`, `natSubRegion`, `natRegionId`, `natSubRegionId`) VALUES
('Afghanistan', 'AF', 'AFG', 4, NULL, 'Asia', 'Southern Asia', 142, 34),
('Albania', 'AL', 'ALB', 8, NULL, 'Europe', 'Southern Europe', 150, 39),
('Antarctica', 'AQ', 'ATA', 10, NULL, NULL, NULL, NULL, NULL),
('Algeria', 'DZ', 'DZA', 12, NULL, 'Africa', 'Northern Africa', 2, 15),
('American Samoa', 'AS', 'ASM', 16, NULL, 'Oceania', 'Polynesia', 9, 61),
('Andorra', 'AD', 'AND', 20, NULL, 'Europe', 'Southern Europe', 150, 39),
('Angola', 'AO', 'AGO', 24, NULL, 'Africa', 'Middle Africa', 2, 17),
('Antigua and Barbuda', 'AG', 'ATG', 28, NULL, 'Americas', 'Caribbean', 19, 29),
('Azerbaijan', 'AZ', 'AZE', 31, NULL, 'Asia', 'Western Asia', 142, 145),
('Argentina', 'AR', 'ARG', 32, NULL, 'Americas', 'South America', 19, 5),
('Australia', 'AU', 'AUS', 36, NULL, 'Oceania', 'Australia and New Zealand', 9, 53),
('Austria', 'AT', 'AUT', 40, NULL, 'Europe', 'Western Europe', 150, 155),
('Bahamas', 'BS', 'BHS', 44, NULL, 'Americas', 'Caribbean', 19, 29),
('Bahrain', 'BH', 'BHR', 48, NULL, 'Asia', 'Western Asia', 142, 145),
('Bangladesh', 'BD', 'BGD', 50, NULL, 'Asia', 'Southern Asia', 142, 34),
('Armenia', 'AM', 'ARM', 51, NULL, 'Asia', 'Western Asia', 142, 145),
('Barbados', 'BB', 'BRB', 52, NULL, 'Americas', 'Caribbean', 19, 29),
('Belgium', 'BE', 'BEL', 56, NULL, 'Europe', 'Western Europe', 150, 155),
('Bermuda', 'BM', 'BMU', 60, NULL, 'Americas', 'Northern America', 19, 21),
('Bhutan', 'BT', 'BTN', 64, NULL, 'Asia', 'Southern Asia', 142, 34),
('Bolivia (Plurinational State of)', 'BO', 'BOL', 68, NULL, 'Americas', 'South America', 19, 5),
('Bosnia and Herzegovina', 'BA', 'BIH', 70, NULL, 'Europe', 'Southern Europe', 150, 39),
('Botswana', 'BW', 'BWA', 72, NULL, 'Africa', 'Southern Africa', 2, 18),
('Bouvet Island', 'BV', 'BVT', 74, NULL, NULL, NULL, NULL, NULL),
('Brazil', 'BR', 'BRA', 76, NULL, 'Americas', 'South America', 19, 5),
('Belize', 'BZ', 'BLZ', 84, NULL, 'Americas', 'Central America', 19, 13),
('British Indian Ocean Territory', 'IO', 'IOT', 86, NULL, NULL, NULL, NULL, NULL),
('Solomon Islands', 'SB', 'SLB', 90, NULL, 'Oceania', 'Melanesia', 9, 54),
('Virgin Islands (British)', 'VG', 'VGB', 92, NULL, 'Americas', 'Caribbean', 19, 29),
('Brunei Darussalam', 'BN', 'BRN', 96, NULL, 'Asia', 'South-Eastern Asia', 142, 35),
('Bulgaria', 'BG', 'BGR', 100, NULL, 'Europe', 'Eastern Europe', 150, 151),
('Myanmar', 'MM', 'MMR', 104, NULL, 'Asia', 'South-Eastern Asia', 142, 35),
('Burundi', 'BI', 'BDI', 108, NULL, 'Africa', 'Eastern Africa', 2, 14),
('Belarus', 'BY', 'BLR', 112, NULL, 'Europe', 'Eastern Europe', 150, 151),
('Cambodia', 'KH', 'KHM', 116, NULL, 'Asia', 'South-Eastern Asia', 142, 35),
('Cameroon', 'CM', 'CMR', 120, NULL, 'Africa', 'Middle Africa', 2, 17),
('Canada', 'CA', 'CAN', 124, NULL, 'Americas', 'Northern America', 19, 21),
('Cabo Verde', 'CV', 'CPV', 132, NULL, 'Africa', 'Western Africa', 2, 11),
('Cayman Islands', 'KY', 'CYM', 136, NULL, 'Americas', 'Caribbean', 19, 29),
('Central African Republic', 'CF', 'CAF', 140, NULL, 'Africa', 'Middle Africa', 2, 17),
('Sri Lanka', 'LK', 'LKA', 144, NULL, 'Asia', 'Southern Asia', 142, 34),
('Chad', 'TD', 'TCD', 148, NULL, 'Africa', 'Middle Africa', 2, 17),
('Chile', 'CL', 'CHL', 152, NULL, 'Americas', 'South America', 19, 5),
('China', 'CN', 'CHN', 156, NULL, 'Asia', 'Eastern Asia', 142, 30),
('Taiwan, Province of China', 'TW', 'TWN', 158, NULL, 'Asia', 'Eastern Asia', 142, 30),
('Christmas Island', 'CX', 'CXR', 162, NULL, NULL, NULL, NULL, NULL),
('Cocos (Keeling) Islands', 'CC', 'CCK', 166, NULL, NULL, NULL, NULL, NULL),
('Colombia', 'CO', 'COL', 170, NULL, 'Americas', 'South America', 19, 5),
('Comoros', 'KM', 'COM', 174, NULL, 'Africa', 'Eastern Africa', 2, 14),
('Mayotte', 'YT', 'MYT', 175, NULL, 'Africa', 'Eastern Africa', 2, 14),
('Congo', 'CG', 'COG', 178, NULL, 'Africa', 'Middle Africa', 2, 17),
('Congo (Democratic Republic of the)', 'CD', 'COD', 180, NULL, 'Africa', 'Middle Africa', 2, 17),
('Cook Islands', 'CK', 'COK', 184, NULL, 'Oceania', 'Polynesia', 9, 61),
('Costa Rica', 'CR', 'CRI', 188, NULL, 'Americas', 'Central America', 19, 13),
('Croatia', 'HR', 'HRV', 191, NULL, 'Europe', 'Southern Europe', 150, 39),
('Cuba', 'CU', 'CUB', 192, NULL, 'Americas', 'Caribbean', 19, 29),
('Cyprus', 'CY', 'CYP', 196, NULL, 'Asia', 'Western Asia', 142, 145),
('Czech Republic', 'CZ', 'CZE', 203, NULL, 'Europe', 'Eastern Europe', 150, 151),
('Benin', 'BJ', 'BEN', 204, NULL, 'Africa', 'Western Africa', 2, 11),
('Denmark', 'DK', 'DNK', 208, NULL, 'Europe', 'Northern Europe', 150, 154),
('Dominica', 'DM', 'DMA', 212, NULL, 'Americas', 'Caribbean', 19, 29),
('Dominican Republic', 'DO', 'DOM', 214, NULL, 'Americas', 'Caribbean', 19, 29),
('Ecuador', 'EC', 'ECU', 218, NULL, 'Americas', 'South America', 19, 5),
('El Salvador', 'SV', 'SLV', 222, NULL, 'Americas', 'Central America', 19, 13),
('Equatorial Guinea', 'GQ', 'GNQ', 226, NULL, 'Africa', 'Middle Africa', 2, 17),
('Ethiopia', 'ET', 'ETH', 231, NULL, 'Africa', 'Eastern Africa', 2, 14),
('Eritrea', 'ER', 'ERI', 232, NULL, 'Africa', 'Eastern Africa', 2, 14),
('Estonia', 'EE', 'EST', 233, NULL, 'Europe', 'Northern Europe', 150, 154),
('Faroe Islands', 'FO', 'FRO', 234, NULL, 'Europe', 'Northern Europe', 150, 154),
('Falkland Islands (Malvinas)', 'FK', 'FLK', 238, NULL, 'Americas', 'South America', 19, 5),
('South Georgia and the South Sandwich Islands', 'GS', 'SGS', 239, NULL, NULL, NULL, NULL, NULL),
('Fiji', 'FJ', 'FJI', 242, NULL, 'Oceania', 'Melanesia', 9, 54),
('Finland', 'FI', 'FIN', 246, NULL, 'Europe', 'Northern Europe', 150, 154),
('Åland Islands', 'AX', 'ALA', 248, NULL, 'Europe', 'Northern Europe', 150, 154),
('France', 'FR', 'FRA', 250, NULL, 'Europe', 'Western Europe', 150, 155),
('French Guiana', 'GF', 'GUF', 254, NULL, 'Americas', 'South America', 19, 5),
('French Polynesia', 'PF', 'PYF', 258, NULL, 'Oceania', 'Polynesia', 9, 61),
('French Southern Territories', 'TF', 'ATF', 260, NULL, NULL, NULL, NULL, NULL),
('Djibouti', 'DJ', 'DJI', 262, NULL, 'Africa', 'Eastern Africa', 2, 14),
('Gabon', 'GA', 'GAB', 266, NULL, 'Africa', 'Middle Africa', 2, 17),
('Georgia', 'GE', 'GEO', 268, NULL, 'Asia', 'Western Asia', 142, 145),
('Gambia', 'GM', 'GMB', 270, NULL, 'Africa', 'Western Africa', 2, 11),
('Palestine, State of', 'PS', 'PSE', 275, NULL, 'Asia', 'Western Asia', 142, 145),
('Germany', 'DE', 'DEU', 276, NULL, 'Europe', 'Western Europe', 150, 155),
('Ghana', 'GH', 'GHA', 288, NULL, 'Africa', 'Western Africa', 2, 11),
('Gibraltar', 'GI', 'GIB', 292, NULL, 'Europe', 'Southern Europe', 150, 39),
('Kiribati', 'KI', 'KIR', 296, NULL, 'Oceania', 'Micronesia', 9, 57),
('Greece', 'GR', 'GRC', 300, NULL, 'Europe', 'Southern Europe', 150, 39),
('Greenland', 'GL', 'GRL', 304, NULL, 'Americas', 'Northern America', 19, 21),
('Grenada', 'GD', 'GRD', 308, NULL, 'Americas', 'Caribbean', 19, 29),
('Guadeloupe', 'GP', 'GLP', 312, NULL, 'Americas', 'Caribbean', 19, 29),
('Guam', 'GU', 'GUM', 316, NULL, 'Oceania', 'Micronesia', 9, 57),
('Guatemala', 'GT', 'GTM', 320, NULL, 'Americas', 'Central America', 19, 13),
('Guinea', 'GN', 'GIN', 324, NULL, 'Africa', 'Western Africa', 2, 11),
('Guyana', 'GY', 'GUY', 328, NULL, 'Americas', 'South America', 19, 5),
('Haiti', 'HT', 'HTI', 332, NULL, 'Americas', 'Caribbean', 19, 29),
('Heard Island and McDonald Islands', 'HM', 'HMD', 334, NULL, NULL, NULL, NULL, NULL),
('Holy See', 'VA', 'VAT', 336, NULL, 'Europe', 'Southern Europe', 150, 39),
('Honduras', 'HN', 'HND', 340, NULL, 'Americas', 'Central America', 19, 13),
('Hong Kong', 'HK', 'HKG', 344, NULL, 'Asia', 'Eastern Asia', 142, 30),
('Hungary', 'HU', 'HUN', 348, NULL, 'Europe', 'Eastern Europe', 150, 151),
('Iceland', 'IS', 'ISL', 352, NULL, 'Europe', 'Northern Europe', 150, 154),
('India', 'IN', 'IND', 356, NULL, 'Asia', 'Southern Asia', 142, 34),
('Indonesia', 'ID', 'IDN', 360, NULL, 'Asia', 'South-Eastern Asia', 142, 35),
('Iran (Islamic Republic of)', 'IR', 'IRN', 364, NULL, 'Asia', 'Southern Asia', 142, 34),
('Iraq', 'IQ', 'IRQ', 368, NULL, 'Asia', 'Western Asia', 142, 145),
('Ireland', 'IE', 'IRL', 372, NULL, 'Europe', 'Northern Europe', 150, 154),
('Israel', 'IL', 'ISR', 376, NULL, 'Asia', 'Western Asia', 142, 145),
('Italy', 'IT', 'ITA', 380, NULL, 'Europe', 'Southern Europe', 150, 39),
('Côte d\'Ivoire', 'CI', 'CIV', 384, NULL, 'Africa', 'Western Africa', 2, 11),
('Jamaica', 'JM', 'JAM', 388, NULL, 'Americas', 'Caribbean', 19, 29),
('Japan', 'JP', 'JPN', 392, NULL, 'Asia', 'Eastern Asia', 142, 30),
('Kazakhstan', 'KZ', 'KAZ', 398, NULL, 'Asia', 'Central Asia', 142, 143),
('Jordan', 'JO', 'JOR', 400, NULL, 'Asia', 'Western Asia', 142, 145),
('Kenya', 'KE', 'KEN', 404, NULL, 'Africa', 'Eastern Africa', 2, 14),
('Korea (Democratic People\'s Republic of)', 'KP', 'PRK', 408, NULL, 'Asia', 'Eastern Asia', 142, 30),
('Korea (Republic of)', 'KR', 'KOR', 410, NULL, 'Asia', 'Eastern Asia', 142, 30),
('Kuwait', 'KW', 'KWT', 414, NULL, 'Asia', 'Western Asia', 142, 145),
('Kyrgyzstan', 'KG', 'KGZ', 417, NULL, 'Asia', 'Central Asia', 142, 143),
('Lao People\'s Democratic Republic', 'LA', 'LAO', 418, NULL, 'Asia', 'South-Eastern Asia', 142, 35),
('Lebanon', 'LB', 'LBN', 422, NULL, 'Asia', 'Western Asia', 142, 145),
('Lesotho', 'LS', 'LSO', 426, NULL, 'Africa', 'Southern Africa', 2, 18),
('Latvia', 'LV', 'LVA', 428, NULL, 'Europe', 'Northern Europe', 150, 154),
('Liberia', 'LR', 'LBR', 430, NULL, 'Africa', 'Western Africa', 2, 11),
('Libya', 'LY', 'LBY', 434, NULL, 'Africa', 'Northern Africa', 2, 15),
('Liechtenstein', 'LI', 'LIE', 438, NULL, 'Europe', 'Western Europe', 150, 155),
('Lithuania', 'LT', 'LTU', 440, NULL, 'Europe', 'Northern Europe', 150, 154),
('Luxembourg', 'LU', 'LUX', 442, NULL, 'Europe', 'Western Europe', 150, 155),
('Macao', 'MO', 'MAC', 446, NULL, 'Asia', 'Eastern Asia', 142, 30),
('Madagascar', 'MG', 'MDG', 450, NULL, 'Africa', 'Eastern Africa', 2, 14),
('Malawi', 'MW', 'MWI', 454, NULL, 'Africa', 'Eastern Africa', 2, 14),
('Malaysia', 'MY', 'MYS', 458, NULL, 'Asia', 'South-Eastern Asia', 142, 35),
('Maldives', 'MV', 'MDV', 462, NULL, 'Asia', 'Southern Asia', 142, 34),
('Mali', 'ML', 'MLI', 466, NULL, 'Africa', 'Western Africa', 2, 11),
('Malta', 'MT', 'MLT', 470, NULL, 'Europe', 'Southern Europe', 150, 39),
('Martinique', 'MQ', 'MTQ', 474, NULL, 'Americas', 'Caribbean', 19, 29),
('Mauritania', 'MR', 'MRT', 478, NULL, 'Africa', 'Western Africa', 2, 11),
('Mauritius', 'MU', 'MUS', 480, NULL, 'Africa', 'Eastern Africa', 2, 14),
('Mexico', 'MX', 'MEX', 484, NULL, 'Americas', 'Central America', 19, 13),
('Monaco', 'MC', 'MCO', 492, NULL, 'Europe', 'Western Europe', 150, 155),
('Mongolia', 'MN', 'MNG', 496, NULL, 'Asia', 'Eastern Asia', 142, 30),
('Moldova (Republic of)', 'MD', 'MDA', 498, NULL, 'Europe', 'Eastern Europe', 150, 151),
('Montenegro', 'ME', 'MNE', 499, NULL, 'Europe', 'Southern Europe', 150, 39),
('Montserrat', 'MS', 'MSR', 500, NULL, 'Americas', 'Caribbean', 19, 29),
('Morocco', 'MA', 'MAR', 504, NULL, 'Africa', 'Northern Africa', 2, 15),
('Mozambique', 'MZ', 'MOZ', 508, NULL, 'Africa', 'Eastern Africa', 2, 14),
('Oman', 'OM', 'OMN', 512, NULL, 'Asia', 'Western Asia', 142, 145),
('Namibia', 'NA', 'NAM', 516, NULL, 'Africa', 'Southern Africa', 2, 18),
('Nauru', 'NR', 'NRU', 520, NULL, 'Oceania', 'Micronesia', 9, 57),
('Nepal', 'NP', 'NPL', 524, NULL, 'Asia', 'Southern Asia', 142, 34),
('Netherlands', 'NL', 'NLD', 528, NULL, 'Europe', 'Western Europe', 150, 155),
('Curaçao', 'CW', 'CUW', 531, NULL, 'Americas', 'Caribbean', 19, 29),
('Aruba', 'AW', 'ABW', 533, NULL, 'Americas', 'Caribbean', 19, 29),
('Sint Maarten (Dutch part)', 'SX', 'SXM', 534, NULL, 'Americas', 'Caribbean', 19, 29),
('Bonaire, Sint Eustatius and Saba', 'BQ', 'BES', 535, NULL, 'Americas', 'Caribbean', 19, 29),
('New Caledonia', 'NC', 'NCL', 540, NULL, 'Oceania', 'Melanesia', 9, 54),
('Vanuatu', 'VU', 'VUT', 548, NULL, 'Oceania', 'Melanesia', 9, 54),
('New Zealand', 'NZ', 'NZL', 554, NULL, 'Oceania', 'Australia and New Zealand', 9, 53),
('Nicaragua', 'NI', 'NIC', 558, NULL, 'Americas', 'Central America', 19, 13),
('Niger', 'NE', 'NER', 562, NULL, 'Africa', 'Western Africa', 2, 11),
('Nigeria', 'NG', 'NGA', 566, NULL, 'Africa', 'Western Africa', 2, 11),
('Niue', 'NU', 'NIU', 570, NULL, 'Oceania', 'Polynesia', 9, 61),
('Norfolk Island', 'NF', 'NFK', 574, NULL, 'Oceania', 'Australia and New Zealand', 9, 53),
('Norway', 'NO', 'NOR', 578, NULL, 'Europe', 'Northern Europe', 150, 154),
('Northern Mariana Islands', 'MP', 'MNP', 580, NULL, 'Oceania', 'Micronesia', 9, 57),
('United States Minor Outlying Islands', 'UM', 'UMI', 581, NULL, NULL, NULL, NULL, NULL),
('Micronesia (Federated States of)', 'FM', 'FSM', 583, NULL, 'Oceania', 'Micronesia', 9, 57),
('Marshall Islands', 'MH', 'MHL', 584, NULL, 'Oceania', 'Micronesia', 9, 57),
('Palau', 'PW', 'PLW', 585, NULL, 'Oceania', 'Micronesia', 9, 57),
('Pakistan', 'PK', 'PAK', 586, NULL, 'Asia', 'Southern Asia', 142, 34),
('Panama', 'PA', 'PAN', 591, NULL, 'Americas', 'Central America', 19, 13),
('Papua New Guinea', 'PG', 'PNG', 598, NULL, 'Oceania', 'Melanesia', 9, 54),
('Paraguay', 'PY', 'PRY', 600, NULL, 'Americas', 'South America', 19, 5),
('Peru', 'PE', 'PER', 604, NULL, 'Americas', 'South America', 19, 5),
('Philippines', 'PH', 'PHL', 608, NULL, 'Asia', 'South-Eastern Asia', 142, 35),
('Pitcairn', 'PN', 'PCN', 612, NULL, 'Oceania', 'Polynesia', 9, 61),
('Poland', 'PL', 'POL', 616, NULL, 'Europe', 'Eastern Europe', 150, 151),
('Portugal', 'PT', 'PRT', 620, NULL, 'Europe', 'Southern Europe', 150, 39),
('Guinea-Bissau', 'GW', 'GNB', 624, NULL, 'Africa', 'Western Africa', 2, 11),
('Timor-Leste', 'TL', 'TLS', 626, NULL, 'Asia', 'South-Eastern Asia', 142, 35),
('Puerto Rico', 'PR', 'PRI', 630, NULL, 'Americas', 'Caribbean', 19, 29),
('Qatar', 'QA', 'QAT', 634, NULL, 'Asia', 'Western Asia', 142, 145),
('Réunion', 'RE', 'REU', 638, NULL, 'Africa', 'Eastern Africa', 2, 14),
('Romania', 'RO', 'ROU', 642, NULL, 'Europe', 'Eastern Europe', 150, 151),
('Russian Federation', 'RU', 'RUS', 643, NULL, 'Europe', 'Eastern Europe', 150, 151),
('Rwanda', 'RW', 'RWA', 646, NULL, 'Africa', 'Eastern Africa', 2, 14),
('Saint Barthélemy', 'BL', 'BLM', 652, NULL, 'Americas', 'Caribbean', 19, 29),
('Saint Helena, Ascension and Tristan da Cunha', 'SH', 'SHN', 654, NULL, 'Africa', 'Western Africa', 2, 11),
('Saint Kitts and Nevis', 'KN', 'KNA', 659, NULL, 'Americas', 'Caribbean', 19, 29),
('Anguilla', 'AI', 'AIA', 660, NULL, 'Americas', 'Caribbean', 19, 29),
('Saint Lucia', 'LC', 'LCA', 662, NULL, 'Americas', 'Caribbean', 19, 29),
('Saint Martin (French part)', 'MF', 'MAF', 663, NULL, 'Americas', 'Caribbean', 19, 29),
('Saint Pierre and Miquelon', 'PM', 'SPM', 666, NULL, 'Americas', 'Northern America', 19, 21),
('Saint Vincent and the Grenadines', 'VC', 'VCT', 670, NULL, 'Americas', 'Caribbean', 19, 29),
('San Marino', 'SM', 'SMR', 674, NULL, 'Europe', 'Southern Europe', 150, 39),
('Sao Tome and Principe', 'ST', 'STP', 678, NULL, 'Africa', 'Middle Africa', 2, 17),
('Saudi Arabia', 'SA', 'SAU', 682, NULL, 'Asia', 'Western Asia', 142, 145),
('Senegal', 'SN', 'SEN', 686, NULL, 'Africa', 'Western Africa', 2, 11),
('Serbia', 'RS', 'SRB', 688, NULL, 'Europe', 'Southern Europe', 150, 39),
('Seychelles', 'SC', 'SYC', 690, NULL, 'Africa', 'Eastern Africa', 2, 14),
('Sierra Leone', 'SL', 'SLE', 694, NULL, 'Africa', 'Western Africa', 2, 11),
('Singapore', 'SG', 'SGP', 702, NULL, 'Asia', 'South-Eastern Asia', 142, 35),
('Slovakia', 'SK', 'SVK', 703, NULL, 'Europe', 'Eastern Europe', 150, 151),
('Viet Nam', 'VN', 'VNM', 704, NULL, 'Asia', 'South-Eastern Asia', 142, 35),
('Slovenia', 'SI', 'SVN', 705, NULL, 'Europe', 'Southern Europe', 150, 39),
('Somalia', 'SO', 'SOM', 706, NULL, 'Africa', 'Eastern Africa', 2, 14),
('South Africa', 'ZA', 'ZAF', 710, NULL, 'Africa', 'Southern Africa', 2, 18),
('Zimbabwe', 'ZW', 'ZWE', 716, NULL, 'Africa', 'Eastern Africa', 2, 14),
('Spain', 'ES', 'ESP', 724, NULL, 'Europe', 'Southern Europe', 150, 39),
('South Sudan', 'SS', 'SSD', 728, NULL, 'Africa', 'Eastern Africa', 2, 14),
('Sudan', 'SD', 'SDN', 729, NULL, 'Africa', 'Northern Africa', 2, 15),
('Western Sahara', 'EH', 'ESH', 732, NULL, 'Africa', 'Northern Africa', 2, 15),
('Suriname', 'SR', 'SUR', 740, NULL, 'Americas', 'South America', 19, 5),
('Svalbard and Jan Mayen', 'SJ', 'SJM', 744, NULL, 'Europe', 'Northern Europe', 150, 154),
('Swaziland', 'SZ', 'SWZ', 748, NULL, 'Africa', 'Southern Africa', 2, 18),
('Sweden', 'SE', 'SWE', 752, NULL, 'Europe', 'Northern Europe', 150, 154),
('Switzerland', 'CH', 'CHE', 756, NULL, 'Europe', 'Western Europe', 150, 155),
('Syrian Arab Republic', 'SY', 'SYR', 760, NULL, 'Asia', 'Western Asia', 142, 145),
('Tajikistan', 'TJ', 'TJK', 762, NULL, 'Asia', 'Central Asia', 142, 143),
('Thailand', 'TH', 'THA', 764, NULL, 'Asia', 'South-Eastern Asia', 142, 35),
('Togo', 'TG', 'TGO', 768, NULL, 'Africa', 'Western Africa', 2, 11),
('Tokelau', 'TK', 'TKL', 772, NULL, 'Oceania', 'Polynesia', 9, 61),
('Tonga', 'TO', 'TON', 776, NULL, 'Oceania', 'Polynesia', 9, 61),
('Trinidad and Tobago', 'TT', 'TTO', 780, NULL, 'Americas', 'Caribbean', 19, 29),
('United Arab Emirates', 'AE', 'ARE', 784, NULL, 'Asia', 'Western Asia', 142, 145),
('Tunisia', 'TN', 'TUN', 788, NULL, 'Africa', 'Northern Africa', 2, 15),
('Turkey', 'TR', 'TUR', 792, NULL, 'Asia', 'Western Asia', 142, 145),
('Turkmenistan', 'TM', 'TKM', 795, NULL, 'Asia', 'Central Asia', 142, 143),
('Turks and Caicos Islands', 'TC', 'TCA', 796, NULL, 'Americas', 'Caribbean', 19, 29),
('Tuvalu', 'TV', 'TUV', 798, NULL, 'Oceania', 'Polynesia', 9, 61),
('Uganda', 'UG', 'UGA', 800, NULL, 'Africa', 'Eastern Africa', 2, 14),
('Ukraine', 'UA', 'UKR', 804, NULL, 'Europe', 'Eastern Europe', 150, 151),
('Macedonia (the former Yugoslav Republic of)', 'MK', 'MKD', 807, NULL, 'Europe', 'Southern Europe', 150, 39),
('Egypt', 'EG', 'EGY', 818, NULL, 'Africa', 'Northern Africa', 2, 15),
('United Kingdom of Great Britain and Northern Ireland', 'GB', 'GBR', 826, NULL, 'Europe', 'Northern Europe', 150, 154),
('Guernsey', 'GG', 'GGY', 831, NULL, 'Europe', 'Northern Europe', 150, 154),
('Jersey', 'JE', 'JEY', 832, NULL, 'Europe', 'Northern Europe', 150, 154),
('Isle of Man', 'IM', 'IMN', 833, NULL, 'Europe', 'Northern Europe', 150, 154),
('Tanzania, United Republic of', 'TZ', 'TZA', 834, NULL, 'Africa', 'Eastern Africa', 2, 14),
('United States of America', 'US', 'USA', 840, NULL, 'Americas', 'Northern America', 19, 21),
('Virgin Islands (U.S.)', 'VI', 'VIR', 850, NULL, 'Americas', 'Caribbean', 19, 29),
('Burkina Faso', 'BF', 'BFA', 854, NULL, 'Africa', 'Western Africa', 2, 11),
('Uruguay', 'UY', 'URY', 858, NULL, 'Americas', 'South America', 19, 5),
('Uzbekistan', 'UZ', 'UZB', 860, NULL, 'Asia', 'Central Asia', 142, 143),
('Venezuela (Bolivarian Republic of)', 'VE', 'VEN', 862, NULL, 'Americas', 'South America', 19, 5),
('Wallis and Futuna', 'WF', 'WLF', 876, NULL, 'Oceania', 'Polynesia', 9, 61),
('Samoa', 'WS', 'WSM', 882, NULL, 'Oceania', 'Polynesia', 9, 61),
('Yemen', 'YE', 'YEM', 887, NULL, 'Asia', 'Western Asia', 142, 145),
('Zambia', 'ZM', 'ZMB', 894, NULL, 'Africa', 'Eastern Africa', 2, 14);

--
-- Indexes for dumped tables
--


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
  `name` varchar(12) NOT NULL,
  `rwp_id` int(11) DEFAULT NULL,
  `lat` float NOT NULL,
  `lon` float NOT NULL,
  `altitude` smallint(6) NOT NULL DEFAULT '0',
  `description` varchar(64) DEFAULT NULL,
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

CREATE ALGORITHM=UNDEFINED DEFINER=CURRENT_USER SQL SECURITY DEFINER VIEW `CompObjectView`  AS  select `C`.`comp_id` AS `comp_id`,`C`.`comp_name` AS `comp_name`,`C`.`comp_site` AS `comp_site`,`C`.`date_from` AS `date_from`,`C`.`date_to` AS `date_to`,`C`.`MD_name` AS `MD_name`,`C`.`contact` AS `contact`,`C`.`cat_id` AS `cat_id`,`C`.`sanction` AS `sanction`,`C`.`comp_type` AS `comp_type`,`C`.`comp_code` AS `comp_code`,`C`.`restricted` AS `restricted`,`C`.`time_offset` AS `time_offset`,`C`.`comp_class` AS `comp_class`,`C`.`openair_file` AS `openair_file`,`C`.`stylesheet` AS `stylesheet`,`C`.`locked` AS `locked`,`C`.`comp_path` AS `comp_path`,`C`.`external` AS `external`,`C`.`website` AS `website`,`C`.`airspace_check` AS `airspace_check`,`C`.`check_launch` AS `check_launch`,`C`.`igc_config_file` AS `igc_config_file`,`C`.`self_register` AS `self_register`,`C`.`check_g_record` AS `check_g_record`,`C`.`track_source` AS `track_source`,`FC`.`formula_type` AS `formula_type`,`FC`.`formula_version` AS `formula_version`,ifnull(`FC`.`external_name`,ifnull(`FC`.`formula_name`,concat(upper(`FC`.`formula_type`),`FC`.`formula_version`))) AS `formula_name`,`FC`.`overall_validity` AS `overall_validity`,`FC`.`validity_param` AS `validity_param`,`FC`.`validity_ref` AS `validity_ref`,`FC`.`nominal_goal` AS `nominal_goal`,`FC`.`min_dist` AS `min_dist`,`FC`.`nominal_dist` AS `nominal_dist`,`FC`.`nominal_time` AS `nominal_time`,`FC`.`nominal_launch` AS `nominal_launch`,`FC`.`formula_distance` AS `formula_distance`,`FC`.`formula_arrival` AS `formula_arrival`,`FC`.`formula_departure` AS `formula_departure`,`FC`.`lead_factor` AS `lead_factor`,`FC`.`formula_time` AS `formula_time`,`FC`.`no_goal_penalty` AS `no_goal_penalty`,`FC`.`glide_bonus` AS `glide_bonus`,`FC`.`tolerance` AS `tolerance`,`FC`.`min_tolerance` AS `min_tolerance`,`FC`.`arr_alt_bonus` AS `arr_alt_bonus`,`FC`.`arr_min_height` AS `arr_min_height`,`FC`.`arr_max_height` AS `arr_max_height`,`FC`.`validity_min_time` AS `validity_min_time`,`FC`.`score_back_time` AS `score_back_time`,`FC`.`max_JTG` AS `max_JTG`,`FC`.`JTG_penalty_per_sec` AS `JTG_penalty_per_sec`,`FC`.`scoring_altitude` AS `scoring_altitude`,`FC`.`task_result_decimal` AS `task_result_decimal`,`FC`.`comp_result_decimal` AS `comp_result_decimal`,`FC`.`team_scoring` AS `team_scoring`,`FC`.`team_size` AS `team_size`,`FC`.`max_team_size` AS `max_team_size`,`FC`.`country_scoring` AS `country_scoring`,`FC`.`country_size` AS `country_size`,`FC`.`max_country_size` AS `max_country_size`,`FC`.`team_over` AS `team_over` from (`tblCompetition` `C` left join `tblForComp` `FC` on((`C`.`comp_id` = `FC`.`comp_id`))) order by (case when (`C`.`comp_name` like '%test%') then `C`.`comp_name` else `C`.`date_to` end) desc ;

-- --------------------------------------------------------

--
-- Structure for view `FlightResultView`
--
DROP TABLE IF EXISTS `FlightResultView`;

CREATE ALGORITHM=UNDEFINED DEFINER=CURRENT_USER SQL SECURITY DEFINER VIEW `FlightResultView`  AS  select `T`.`track_id` AS `track_id`,`T`.`par_id` AS `par_id`,`T`.`task_id` AS `task_id`,`R`.`comp_id` AS `comp_id`,`R`.`civl_id` AS `civl_id`,`R`.`fai_id` AS `fai_id`,`R`.`pil_id` AS `pil_id`,`R`.`ID` AS `ID`,`R`.`name` AS `name`,`R`.`nat` AS `nat`,`R`.`sex` AS `sex`,`R`.`glider` AS `glider`,`R`.`glider_cert` AS `glider_cert`,`R`.`sponsor` AS `sponsor`,`R`.`team` AS `team`,`R`.`nat_team` AS `nat_team`,`R`.`live_id` AS `live_id`,`T`.`distance_flown` AS `distance_flown`,`T`.`best_distance_time` AS `best_distance_time`,`T`.`stopped_distance` AS `stopped_distance`,`T`.`stopped_altitude` AS `stopped_altitude`,`T`.`total_distance` AS `total_distance`,`T`.`speed` AS `speed`,`T`.`first_time` AS `first_time`,`T`.`real_start_time` AS `real_start_time`,`T`.`goal_time` AS `goal_time`,`T`.`last_time` AS `last_time`,`T`.`result_type` AS `result_type`,`T`.`SSS_time` AS `SSS_time`,`T`.`ESS_time` AS `ESS_time`,`T`.`waypoints_made` AS `waypoints_made`,`T`.`penalty` AS `penalty`,`T`.`comment` AS `comment`,`T`.`time_score` AS `time_score`,`T`.`distance_score` AS `distance_score`,`T`.`arrival_score` AS `arrival_score`,`T`.`departure_score` AS `departure_score`,`T`.`score` AS `score`,`T`.`lead_coeff` AS `lead_coeff`,`T`.`fixed_LC` AS `fixed_LC`,`T`.`ESS_altitude` AS `ESS_altitude`,`T`.`goal_altitude` AS `goal_altitude`,`T`.`max_altitude` AS `max_altitude`,`T`.`last_altitude` AS `last_altitude`,`T`.`landing_altitude` AS `landing_altitude`,`T`.`landing_time` AS `landing_time`,`T`.`track_file` AS `track_file`,`T`.`g_record` AS `g_record` from (`tblTaskResult` `T` join `tblParticipant` `R` on((`T`.`par_id` = `R`.`par_id`))) order by `T`.`task_id`,`T`.`score` desc ;

-- --------------------------------------------------------

--
-- Structure for view `RegionWaypointView`
--
DROP TABLE IF EXISTS `RegionWaypointView`;

CREATE ALGORITHM=UNDEFINED DEFINER=CURRENT_USER SQL SECURITY DEFINER VIEW `RegionWaypointView`  AS  select `tblRegionWaypoint`.`rwp_id` AS `rwp_id`,`tblRegionWaypoint`.`reg_id` AS `region_id`,`tblRegionWaypoint`.`name` AS `name`,`tblRegionWaypoint`.`lat` AS `lat`,`tblRegionWaypoint`.`lon` AS `lon`,`tblRegionWaypoint`.`altitude` AS `altitude`,`tblRegionWaypoint`.`description` AS `description` from `tblRegionWaypoint` where (`tblRegionWaypoint`.`old` = 0) ;

-- --------------------------------------------------------

--
-- Structure for view `TaskAirspaceCheckView`
--
DROP TABLE IF EXISTS `TaskAirspaceCheckView`;

CREATE ALGORITHM=UNDEFINED DEFINER=CURRENT_USER SQL SECURITY DEFINER VIEW `TaskAirspaceCheckView`  AS  select `T`.`task_id` AS `task_id`,`T`.`airspace_check` AS `airspace_check`,`A`.`notification_distance` AS `notification_distance`,`A`.`function` AS `function`,`A`.`h_outer_limit` AS `h_outer_limit`,`A`.`h_inner_limit` AS `h_inner_limit`,`A`.`h_boundary` AS `h_boundary`,`A`.`h_boundary_penalty` AS `h_boundary_penalty`,`A`.`h_max_penalty` AS `h_max_penalty`,`A`.`v_outer_limit` AS `v_outer_limit`,`A`.`v_inner_limit` AS `v_inner_limit`,`A`.`v_boundary` AS `v_boundary`,`A`.`v_boundary_penalty` AS `v_boundary_penalty`,`A`.`v_max_penalty` AS `v_max_penalty` from ((`tblTask` `T` join `tblCompetition` `C` on((`T`.`comp_id` = `C`.`comp_id`))) left join `tblCompAirspaceCheck` `A` on((`T`.`comp_id` = `A`.`comp_id`))) order by `T`.`task_id` ;

-- --------------------------------------------------------

--
-- Structure for view `TaskFormulaView`
--
DROP TABLE IF EXISTS `TaskFormulaView`;

CREATE ALGORITHM=UNDEFINED DEFINER=CURRENT_USER SQL SECURITY DEFINER VIEW `TaskFormulaView`  AS  select `FC`.`comp_id` AS `comp_id`,`T`.`task_id` AS `task_id`,`FC`.`formula_type` AS `formula_type`,`FC`.`formula_version` AS `formula_version`,ifnull(`FC`.`external_name`,ifnull(`FC`.`formula_name`,concat(upper(`FC`.`formula_type`),`FC`.`formula_version`))) AS `formula_name`,`FC`.`overall_validity` AS `overall_validity`,`FC`.`validity_param` AS `validity_param`,`FC`.`validity_ref` AS `validity_ref`,`FC`.`nominal_goal` AS `nominal_goal`,`FC`.`min_dist` AS `min_dist`,`FC`.`nominal_dist` AS `nominal_dist`,`FC`.`nominal_time` AS `nominal_time`,`FC`.`nominal_launch` AS `nominal_launch`,`T`.`formula_distance` AS `formula_distance`,`T`.`formula_departure` AS `formula_departure`,`T`.`formula_arrival` AS `formula_arrival`,`T`.`formula_time` AS `formula_time`,`FC`.`lead_factor` AS `lead_factor`,`T`.`no_goal_penalty` AS `no_goal_penalty`,`FC`.`glide_bonus` AS `glide_bonus`,`T`.`tolerance` AS `tolerance`,`FC`.`min_tolerance` AS `min_tolerance`,`T`.`arr_alt_bonus` AS `arr_alt_bonus`,`FC`.`arr_min_height` AS `arr_min_height`,`FC`.`arr_max_height` AS `arr_max_height`,`FC`.`validity_min_time` AS `validity_min_time`,`FC`.`score_back_time` AS `score_back_time`,`T`.`max_JTG` AS `max_JTG`,`FC`.`JTG_penalty_per_sec` AS `JTG_penalty_per_sec`,`FC`.`scoring_altitude` AS `scoring_altitude`,`FC`.`team_scoring` AS `team_scoring`,`FC`.`team_size` AS `team_size`,`FC`.`max_team_size` AS `max_team_size`,`FC`.`country_scoring` AS `country_scoring`,`FC`.`country_size` AS `country_size`,`FC`.`max_country_size` AS `max_country_size` from (`tblTask` `T` join `tblForComp` `FC` on((`T`.`comp_id` = `FC`.`comp_id`))) order by `T`.`task_id` ;

-- --------------------------------------------------------

--
-- Structure for view `TaskObjectView`
--
DROP TABLE IF EXISTS `TaskObjectView`;

CREATE ALGORITHM=UNDEFINED DEFINER=CURRENT_USER SQL SECURITY DEFINER VIEW `TaskObjectView`  AS  select `T`.`task_id` AS `task_id`,`C`.`comp_code` AS `comp_code`,`C`.`comp_name` AS `comp_name`,`C`.`comp_site` AS `comp_site`,`T`.`time_offset` AS `time_offset`,`C`.`comp_class` AS `comp_class`,`T`.`comp_id` AS `comp_id`,`T`.`date` AS `date`,`T`.`task_name` AS `task_name`,`T`.`task_num` AS `task_num`,`T`.`reg_id` AS `reg_id`,`R`.`description` AS `region_name`,`T`.`window_open_time` AS `window_open_time`,`T`.`task_deadline` AS `task_deadline`,`T`.`window_close_time` AS `window_close_time`,`T`.`check_launch` AS `check_launch`,`T`.`start_time` AS `start_time`,`T`.`SS_interval` AS `SS_interval`,`T`.`start_iteration` AS `start_iteration`,`T`.`start_close_time` AS `start_close_time`,`T`.`stopped_time` AS `stopped_time`,upper(`T`.`task_type`) AS `task_type`,`T`.`distance` AS `distance`,`T`.`opt_dist` AS `opt_dist`,`T`.`opt_dist_to_SS` AS `opt_dist_to_SS`,`T`.`opt_dist_to_ESS` AS `opt_dist_to_ESS`,`T`.`SS_distance` AS `SS_distance`,`T`.`QNH` AS `QNH`,`T`.`comment` AS `comment`,`T`.`locked` AS `locked`,`T`.`airspace_check` AS `airspace_check`,`T`.`openair_file` AS `openair_file`,`T`.`cancelled` AS `cancelled`,`C`.`track_source` AS `track_source`,`T`.`task_path` AS `task_path`,`C`.`comp_path` AS `comp_path`,`C`.`igc_config_file` AS `igc_config_file` from ((`tblTask` `T` join `tblCompetition` `C` on((`T`.`comp_id` = `C`.`comp_id`))) left join `tblRegion` `R` on((`T`.`reg_id` = `R`.`reg_id`))) order by `T`.`date` ;

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
