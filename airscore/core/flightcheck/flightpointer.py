"""
Flight Pointer Library

contains FlightPointer class.

This is a helper class during Flight check. Returns as properties a lot of useful informations, and is responsable to
advance following task route

Properties:
    next:               Turnpoint next waypoint to reach as Turnpoint obj.
    name:               STR label for next Turnpoint (Left Launch, SSS, TPn, ESS, Goal)
    total_number:       INT waypoints number in task route
    type:               STR next Turnpoint.type
    last_made:          Turnpoint last waypoint made
    last_made_index:    INT index of last waypoint made
    start_index:        INT index of start waypoint
    ess_index:          INT index of ess waypoint
    start_done:         BOOL
    ess_done:           BOOL
    made_all:           BOOL route has been completed
    move_to_next:       move pointer to next waypoint in route

- AirScore -
Stuart Mackintosh - Antonio Golfari
2020

"""


class FlightPointer(object):
    def __init__(self, task):
        self.turnpoints = task.turnpoints
        self.optimised_turnpoints = task.optimised_turnpoints
        self.pointer = 0
        self.descriptions = []

        idx = 1
        for tp in self.turnpoints:
            if tp.type == 'launch':
                self.descriptions.append('Left Launch')
            elif tp.type == 'speed':
                self.descriptions.append('SSS')
            elif tp.type == 'endspeed':
                self.descriptions.append('ESS')
            elif tp.type == 'goal':
                self.descriptions.append('Goal')
            elif tp.type == 'waypoint':
                self.descriptions.append(f'TP{str(idx).zfill(2)}')
                idx += 1

    @property
    def next(self):
        return self.turnpoints[self.pointer]

    @property
    def name(self):
        return self.descriptions[self.pointer]

    @property
    def launch(self):
        return next((x for x in self.turnpoints if x.type == 'launch'), None)

    @property
    def goal(self):
        return next((x for x in self.turnpoints if x.type == 'goal'), None)

    @property
    def total_number(self):
        return len(self.turnpoints)

    @property
    def type(self):
        return self.turnpoints[self.pointer].type

    @property
    def last_made(self):
        return self.turnpoints[self.pointer] if self.pointer == 0 else self.turnpoints[self.pointer - 1]

    @property
    def last_made_index(self):
        return 0 if self.pointer == 0 else self.pointer - 1

    @property
    def start_index(self):
        if any(x for x in self.turnpoints if x.type == 'speed'):
            return self.turnpoints.index(next(x for x in self.turnpoints if x.type == 'speed'))
        else:
            return None

    @property
    def ess_index(self):
        if any(x for x in self.turnpoints if x.type == 'endspeed'):
            return self.turnpoints.index(next(x for x in self.turnpoints if x.type == 'endspeed'))
        else:
            return None

    @property
    def start_done(self):
        return self.start_index < self.pointer

    @property
    def ess_done(self):
        return self.ess_index < self.pointer

    @property
    def made_all(self):
        return True if self.pointer == self.total_number else False

    def move_to_next(self):
        if self.pointer < len(self.turnpoints):
            self.pointer += 1

    def done(self):
        self.pointer = self.total_number
