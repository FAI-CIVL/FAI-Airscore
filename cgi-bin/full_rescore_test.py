import igc_lib
import pwc
from task import Task
from flight_result import Flight_result
from myconn import Database
import score_task_test

tasPk = 56
task = Task.read_task(tasPk)
task.calculate_optimised_task_length()
#task.calculate_task_length()
all_results = []
print(task.ShortRouteDistance)

query = "SELECT fc.*, " \
        "fm.* " \
        "FROM airscore.tblTask t left join tblForComp fc " \
        "on t.comPk = fc.comPk left join tblFormula fm " \
        "on fc.forPk = fm.forPk " \
        "where t.tasPk = %s"

with Database() as db:
    formula = db.fetchone(query, [tasPk])
margin = int(formula['forMargin']) * 0.01

query = "select t.traPk, " \
        "t.pilPk, " \
        "t.traFile, " \
        "r.tarSpeedScore, " \
        "r.tarDistanceScore, " \
        "r.tarArrivalScore, " \
        "r.tarDepartureScore, " \
        "r.tarScore " \
        "from tblTaskResult r left join tblTrack t on r.traPk = t.traPk " \
        "where r.tasPk = %s " \
        "and t.traFile is not null"

with Database() as db:
    tracks = db.fetchall(query, [tasPk])

for track in tracks:
    igc_file = track['traFile']
    print(igc_file)
    flight = igc_lib.Flight.create_from_file(igc_file) #load and process igc file
    print(flight.notes)
    task_result= Flight_result.check_flight(flight, task, pwc.parameters, 0.005, 5) #check flight against task with tolerance of 0.05% or 5m
    all_results.append(task_result)
    print(task_result.total_time_str)
    print(task_result.Distance_flown)
    print(task_result.Best_waypoint_achieved)
    task_result.store_result_test(track['traPk'], tasPk)
score_task_test.main(tasPk)





