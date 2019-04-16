"""
Determines how much of a task (and time) is completed
given a particular competition / task 
Use: python3 task_score.py [taskPk] [opt. test]

Antonio Golfari - 2018
"""
# Use your utility module.
import trackUtils
from myconn import Database

import sys, os.path
from pathlib import Path

import gap, pwc, RTG

def create_scoring(formula, test):
    message = ''
    """create the appropriate scoring object"""
    """This part SHOULD BE CHANGED WHEN SCORING SYSTEMS WILL BE A BOX"""
    if formula['Class'] == 'gap':
        message += 'GAP Scoring Formula is used \n'
        scr = gap.new()
    elif formula['Class'] == 'pwc':
        message += 'PWC Scoring Formula is used \n'
        scr = pwc.new()
    elif formula['Class'] == 'RTG':
        message += 'RTG Scoring Formula is used \n'
        scr = RTG.new()
    else:
        message += 'Unknown Scoring Formula. Exiting \n'
        sys.exit()

    taskt = scr.task_totals(task, formula) #???

def main():
    """Main module"""
    test = 0
    """check parameter is good."""
    if len(sys.argv) > 1:
        """Get tasPk"""  
        taskPk = sys.argv[1]
        if len(sys.argv) > 2:
            """Test Mode""" 
            print('Running in TEST MODE')
            test = 1

        """Read the task itself"""
        task = read_task(tasPk, test)

        """Read the formula"""
        formula = read_formula($task['comPk'])

        """Create the scoring object"""
        taskt = create_scoring(formula, test)

        """Now allocate points to pilots"""
        if taskt['pilots'] > 0:
            points_allocation(task, taskt, formula, test)

    else:
        print('error: no task found')

if __name__ == "__main__":
    main()




# Now create the appropriate scoring object ...
if formula->{'class'} == 'gap':
#{

   print "GAP scoring"
       scr = Gap->new()
elif formula->{'class'} == 'pwc':
#{

print "PWC scoring"
    scr = PWC->new()
elif formula->{'class'} == 'RTG':
#{

print "RTG scoring"
    scr = RTG->new()

else:
#{

print Unknown formula class ", formula->{'class'}, "
#    exit 1;


taskt = scr->task_totals(TrackLib::dbh,task,formula)

# Store it in tblTask
#$sql = "update tblTask set tasTotalDistanceFlown=" . $taskt->{'distance'} . 

#           ", tasTotDistOverMin=" . $taskt->{'distovermin'} . 

#            ", tasPilotsTotal=" . $taskt->{'pilots'} . 

#            ", tasPilotsLaunched=" . $taskt->{'launched'} . 

#            ", tasPilotsGoal=" . $taskt->{'goal'} . 

#            ", tasFastestTime=" . $taskt->{'fastest'} . 

#            ", tasMaxDistance=" . $taskt->{'maxdist'} . 

#       " where tasPk=$tasPk";


#print $sql;
sth = TrackLib::dbh->prepare(sql)
#$sth->execute();


# Work out the quality factors (distance, time, launch)

#($dist,$time,$launch, $stop) = $scr->day_quality($taskt, $formula);


# Check if task was stopped - No idea if this is done elsewhere, but without broke PWC.pm
#$task->{'sstopped'} //= 0;

if  task->{'sstopped'} > 0 :
#{

    quality = dist * time * launch * stop
else:
#{

    quality = dist * time * launch
print -- TASK_SCORE -- distQ = dist | timeQ = $time | launchQ = $launch | stopQ = $stop 
print -- TASK_SCORE -- Day Quality = quality 
if quality > 1.0:
#{

    quality = 1.0
#$sth = $TrackLib::dbh->prepare("UPDATE 

#                                   tblTask 

#                               SET 

#                                   tasQuality = '$quality', 

#                                   tasDistQuality = '$dist', 

#                                   tasTimeQuality = '$time', 

#                                   tasLaunchQuality = '$launch', 

#                                   tasStopQuality = '$stop' 

#                               WHERE 

                                    tasPk = 'tasPk'")
#$sth->execute();

taskt->{'quality'} = quality

if taskt->{'pilots'} > 0:
#{

    # Now allocate points to pilots ..
#    $scr->points_allocation($TrackLib::dbh,$task,$taskt,$formula);

