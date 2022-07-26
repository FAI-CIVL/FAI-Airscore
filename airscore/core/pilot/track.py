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

    @staticmethod
    def create_from_file(filename: Path, config: FlightParsingConfig = FlightParsingConfig()):
        """Creates an instance of Flight from a given file.

        Args:
            filename: a string, the name of the input IGC file
            config: a class that implements FlightParsingConfig

        Returns:
            An instance of Flight built from the supplied IGC file.
        """
        # if not config_class:
        #     config = FlightParsingConfig()
        # else:
        #     config = config_class
        fixes = []
        a_records = []
        i_records = []
        h_records = []
        abs_filename = Path(filename).expanduser().absolute()
        with abs_filename.open('r', encoding="ISO-8859-1") as flight_file:
            for line in flight_file:
                line = line.replace('\n', '').replace('\r', '')
                if not line:
                    continue
                if line[0] == 'A':
                    a_records.append(line)
                elif line[0] == 'B':
                    fix = GNSSFix.build_from_B_record(line, index=len(fixes))
                    if fix is not None:
                        if fixes and math.fabs(fix.rawtime - fixes[-1].rawtime) < 1e-5:
                            # The time did not change since the previous fix.
                            # Ignore this fix.
                            pass
                        else:
                            fixes.append(fix)
                elif line[0] == 'I':
                    i_records.append(line)
                elif line[0] == 'H':
                    h_records.append(line)
                else:
                    # Do not parse any other types of IGC records
                    pass
        flight = Flight(fixes, a_records, h_records, i_records, config)
        return flight

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

        fixes = []
        a_records = []
        i_records = []
        h_records = []
        abs_filename = Path(filename).expanduser().absolute()
        with abs_filename.open('r', encoding="ISO-8859-1") as flight_file:
            for line in flight_file:
                line = line.replace('\n', '').replace('\r', '')
                if not line:
                    continue
                if line[0] == 'A':
                    a_records.append(line)
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
                elif line[0] == 'I':
                    i_records.append(line)
                elif line[0] == 'H':
                    h_records.append(line)
                else:
                    # Do not parse any other types of IGC records
                    pass
        try:
            return Flight(fixes, a_records, h_records, i_records, config)
        except IndexError:
            return None
        # return flight

