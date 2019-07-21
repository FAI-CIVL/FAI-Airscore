from task import Task
from pwc import *
from trackDB import read_formula
from trackUtils import Track
from myconn import Database

competitions = []
query = 'SELECT comPk FROM tblCompetition C where comExt =0 '

with Database() as db:
    comps = db.fetchall(query)

#get a list of the comps with pwc formula
for comp in comps:
    formula = read_formula(comp['comPk'])
    if formula['forClass'] == 'pwc':
        competitions.append(comp['comPk'])

query = 'Select * FROM airscore.tblTask where ComPk = %s '

for comp in competitions:
    with Database() as db:
        tasks = db.fetchall(query, [comp])

    for t in tasks:
        if t['tasPk']==16:
            continue
        task = Task.read_task(t['tasPk'])
        formula = read_formula(comp)
        totals = task_totals(task, formula)
        dayQ = day_quality(totals, formula)
        points_weight(task, totals, formula)

        assert (totals['pilots'] == t['tasPilotsLaunched']), "number of pilots does not match for task {}".format(t['tasPk'])
        assert (totals['maxdist'] == t['tasMaxDistance']), "maxdistance for task {} does not match".format(t['tasPk'])
        assert (round(totals['distance'],0) == round(t['tasTotalDistanceFlown'],0)), "TotalDistanceFlown for task {} does not match. ({} v {})".format(t['tasPk'], t['tasTotalDistanceFlown'], totals['distance'])
        assert (round(totals['distovermin'],0) == round(t['tasTotDistOverMin'],0)), "TotDistOverMin for task {} does not match".format(t['tasPk'])
        assert (totals['goal'] == t['tasPilotsGoal']), "tasPilotsGoal for task {} does not match".format(t['tasPk'])
        assert (round(totals['distovermin'],0) == round(t['tasTotDistOverMin'],0)), "TotDistOverMin' for task {} does not match".format(t['tasPk'])

    #     assert taskt['median'] = median
    #     assert taskt['stddev'] = stddev
    #     assert taskt['landed'] = landed
    #     assert taskt['launched'] = launched
    # taskt['launchvalid'] = launchvalid
    # taskt['goal'] = goal
    # taskt['ess'] = ess
    # taskt['fastest'] = fastest
    # taskt['tqtime'] = tqtime
    # taskt['firstdepart'] = mindept
    # taskt['lastdepart'] = lastdept
    # taskt['firstarrival'] = minarr
    # taskt['lastarrival'] = maxarr
    # taskt['mincoeff'] = mincoeff
    # taskt['mincoeff2'] = mincoeff2
    # taskt['distspread'] = distspread


# dayQ = day_quality(totals, formula)
# pWeight = points_weight(task, totals, formula)