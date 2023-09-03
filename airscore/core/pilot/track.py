"""
Track Library

Use:    import track
        par_id = compUtils.get_track_pilot(filename)

This module reads IGC files using igc_lib library
and creates an object containing all info about the flight

Antonio Golfari, Stuart Mackintosh - 2021
"""

import math

from igc_lib import Flight, FlightParsingConfig, GNSSFix
from pathlib2 import Path
from task import Task


class Track(Flight):

    def __init__(self, *args, **kwargs):
        self.relaunch_limit_time = kwargs.pop('relaunch_limit_time', None)
        super().__init__(*args, **kwargs)

    def _check_altitudes(self):
        press_alt_violations_num = 0
        gnss_alt_violations_num = 0
        press_huge_changes_num = 0
        gnss_huge_changes_num = 0
        press_chgs_sum = 0.0
        gnss_chgs_sum = 0.0
        smallint_range = 30000
        press_out_of_range = False
        gnss_out_of_range = False
        for i in range(len(self.fixes) - 1):
            press_alt_delta = math.fabs(
                self.fixes[i+1].press_alt - self.fixes[i].press_alt)
            gnss_alt_delta = math.fabs(
                self.fixes[i+1].gnss_alt - self.fixes[i].gnss_alt)
            rawtime_delta = math.fabs(
                self.fixes[i+1].rawtime - self.fixes[i].rawtime)
            if rawtime_delta > 0.5:
                if (press_alt_delta / rawtime_delta >
                        self._config.max_alt_change_rate):
                    press_huge_changes_num += 1
                else:
                    press_chgs_sum += press_alt_delta
                if (gnss_alt_delta / rawtime_delta >
                        self._config.max_alt_change_rate):
                    gnss_huge_changes_num += 1
                else:
                    gnss_chgs_sum += gnss_alt_delta
            if abs(self.fixes[i].press_alt) > smallint_range:
                press_out_of_range = True
                press_alt_violations_num += 1
            elif (self.fixes[i].press_alt > self._config.max_alt
                    or self.fixes[i].press_alt < self._config.min_alt):
                press_alt_violations_num += 1
            if abs(self.fixes[i].gnss_alt) > smallint_range:
                gnss_out_of_range = True
                gnss_alt_violations_num += 1
            elif (self.fixes[i].gnss_alt > self._config.max_alt or
                    self.fixes[i].gnss_alt < self._config.min_alt):
                gnss_alt_violations_num += 1

        press_chgs_avg = press_chgs_sum / float(len(self.fixes) - 1)
        gnss_chgs_avg = gnss_chgs_sum / float(len(self.fixes) - 1)

        press_alt_ok = True
        if press_out_of_range:
            self.notes.append(
                "Error: pressure altitude is out of smallint range")
            press_alt_ok = False

        if press_chgs_avg < self._config.min_avg_abs_alt_change:
            self.notes.append(
                "Warning: average pressure altitude change between fixes "
                "is: %f. It is lower than the minimum: %f."
                % (press_chgs_avg, self._config.min_avg_abs_alt_change))
            press_alt_ok = False

        if press_huge_changes_num > self._config.max_alt_change_violations:
            self.notes.append(
                "Warning: too many high changes in pressure altitude: %d. "
                "Maximum allowed: %d."
                % (press_huge_changes_num,
                   self._config.max_alt_change_violations))
            press_alt_ok = False

        if press_alt_violations_num > 0:
            self.notes.append(
                "Warning: pressure altitude limits exceeded in %d fixes."
                % (press_alt_violations_num))
            press_alt_ok = False

        gnss_alt_ok = True
        if gnss_out_of_range:
            self.notes.append(
                "Error: gnss altitude is out of smallint range")
            gnss_alt_ok = False

        if gnss_chgs_avg < self._config.min_avg_abs_alt_change:
            self.notes.append(
                "Warning: average gnss altitude change between fixes is: %f. "
                "It is lower than the minimum: %f."
                % (gnss_chgs_avg, self._config.min_avg_abs_alt_change))
            gnss_alt_ok = False

        if gnss_huge_changes_num > self._config.max_alt_change_violations:
            self.notes.append(
                "Warning: too many high changes in gnss altitude: %d. "
                "Maximum allowed: %d."
                % (gnss_huge_changes_num,
                   self._config.max_alt_change_violations))
            gnss_alt_ok = False

        if gnss_alt_violations_num > 0:
            self.notes.append(
                "Warning: gnss altitude limits exceeded in %d fixes." %
                gnss_alt_violations_num)
            gnss_alt_ok = False

        self.press_alt_valid = press_alt_ok
        self.gnss_alt_valid = gnss_alt_ok

    def _compute_takeoff_landing(self):
        """Finds the takeoff and landing fixes in the log.

        Takeoff fix is the first fix in the flying mode. Landing fix
        is the next fix after the last fix in the flying mode or the
        last fix in the file.

        This custom version looks for relaunches if a landing is 
        detected during task window
        """

        from route import distance

        takeoff_fix = None
        landing_fix = None
        was_flying = False
        for fix in self.fixes:
            if fix.flying and takeoff_fix is None:
                takeoff_fix = fix
            elif fix.flying and landing_fix and self.relaunch_limit_time:
                # check if there is a relauch
                max_distance = 400  # maximum distance between launches, meters
                if fix.rawtime < self.relaunch_limit_time and distance(fix, takeoff_fix) < max_distance:
                    # pilot restarts within time limit and inside a reasonable distance from the previous one
                    takeoff_fix = fix
                    landing_fix = None
            if not fix.flying and was_flying:
                landing_fix = fix
                if self.relaunch_limit_time and fix.rawtime < self.relaunch_limit_time:
                    # continue checking if pilot restarts within start window
                    pass
                elif self._config.which_flight_to_pick == "first":
                    # User requested to select just the first flight in the log,
                    # terminate now.
                    break
            was_flying = fix.flying

        if takeoff_fix is None:
            # No takeoff found.
            return

        if landing_fix is None:
            # Landing on the last fix
            landing_fix = self.fixes[-1]

        self.takeoff_fix = takeoff_fix
        self.landing_fix = landing_fix

    @staticmethod
    def create_from_file(filename: Path, config: FlightParsingConfig = FlightParsingConfig()):
        """Creates an instance of Flight from a given file.

        Args:
            filename: a string, the name of the input IGC file
            config: a class that implements FlightParsingConfig

        Returns:
            An instance of Flight built from the supplied IGC file.
        """

        abs_filename = Path(filename).expanduser().absolute()
        with abs_filename.open('r', encoding="ISO-8859-1") as flight_file:
            fixes, a_records, i_records, h_records = parse_igc_file(flight_file)
        return Track(fixes, a_records, h_records, i_records, config)

    @staticmethod
    def process(
            filename: Path,
            task: Task,
            config: FlightParsingConfig = FlightParsingConfig()
    ):
        """Creates an instance of Flight from a given file.
        Trims fixes to the task time range (window_open_time to task_deadline) to avoid problems
        with multiple flights detection.

        Args:
            filename: a string, the name of the input IGC file
            task: Task object
            config: a class that implements FlightParsingConfig

        Returns:
            An instance of Track(igc_lib Flight) built from the supplied IGC file.
        """

        abs_filename = Path(filename).expanduser().absolute()
        with abs_filename.open('r', encoding="ISO-8859-1") as flight_file:
            fixes, a_records, i_records, h_records = parse_igc_file(flight_file, task)
        try:
            return Track(fixes, a_records, h_records, i_records, config, relaunch_limit_time=task.window_close_time or task.start_time)
        except (IndexError, AttributeError) as e:
            print(f"Error creating Track from {filename.name}: {e}")
            return None
        # return flight


def parse_igc_file(lines: list, task: (Task or None) = None) -> tuple:
    fixes = []
    a_records = []
    i_records = []
    h_records = []
    for line in lines:
        line = line.replace('\n', '').replace('\r', '')
        if not line:
            continue
        if line[0] == 'A':
            # Manufacturer and unique ID for FR
            a_records.append(line)
        elif line[0] == 'H':
            # Header record
            h_records.append(line)
        elif line[0] == 'I':
            # FXA extension (mandatory)
            i_records.append(line)
        elif line[0] == 'E' and line[-3:] == 'PEV':
            # trying to catch pilot-initiated events (PEV code) that seem to indicate 
            # detected launch in some GPS instruments
            # this should avoid to consider aborted launch and other events as first flight
            # NOTE: disabled for now, seems not necessary with relaunch detecting code
            # print(f"found a PEV event: {line}")
            # fixes.clear()
            continue
        elif line[0] == 'B':
            fix = GNSSFix.build_from_B_record(line, index=len(fixes))
            if fix is not None:
                if fixes and math.fabs(fix.rawtime - fixes[-1].rawtime) < 1e-5:
                    # The time did not change since the previous fix.
                    # Ignore this fix.
                    pass
                elif task and not (task.window_open_time - 1 <= fix.rawtime <= task.task_deadline + 1):
                    # We are out of task time.
                    # Ignore this fix.
                    pass
                else:
                    fixes.append(fix)
        else:
            # Do not parse any other types of IGC records
            pass

    return fixes, a_records, i_records, h_records
