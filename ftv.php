<?php
require 'authorisation.php';
require 'hc.php';
require 'format.php';

$link = db_connect();
$comPk = intval($_REQUEST['comPk']);

hcheader("Scoring - Fixed Total Validity", 0, "");
echo "<div id=\"content\">";
echo "<div id=\"text\">";
?>
Fixed Total Validity (FTV) is a way of scoring a percentage 
of "your best flying" in a competition. It is similar to selecting
your best X rounds out of a total of Y rounds. But it allows a pilot
to include low validity rounds they have won, which would may otherwise 
be discarded in round by round scoring.

For FTV, there are two separate concepts that are important for each 
task:
<ol>
<li> the <i>validity</i> (GAP task quality) of the task 
<li> how well a pilot flew on each task as a percentage: <i>pilot score / validity</i>
</ol>
In order to generate a score for a pilot we must work out what the
overall validity score for the competition will be.
We do this by summing the validity of each task for the competition and 
multiplying by the given FTV percentage, this is the <i>competition validity</i>. This also gives us the maximum score a 
pilot may have: <i>sum(task validity) * FTV% * 1000</i>. This value defines the 
maximum amount of validity that is included in a pilot's score. This is a similar concept 
to the number of rounds you might score, but instead of counting each round 
as "1" we count rounds between 0-1 and sum these up.
<p>
To determine a pilot's score we sum up their best scores, to do this:
<ol>
<li> A pilot's scores are ordered by how well they flew (see (2) above) on each task.
<li> Scores are then selected from this list until the sum of the validity of the tasks included (not the scores!) for a pilot equals the competition validity. note: this may result in a percentage of a task being included in order to match the competition validity.
<li> The scores of the tasks included for a particular pilot are then summed to get their overall score.
</ol>
<p>
The net effect of this scoring is that a pilot who flies well on bad days can include more of these bad days (low validity) in their total score than a pilot who only flies well on good days (high validity) and still get the same overall score. 
<?php
echo "</div>";
//echo "<div id=\"image\"><img src=\"images/pilots.jpg\" alt=\"Pilots Flying\"/></div>";
echo "<div id=\"sideBar\">";
hcregion($link);
hcopencomps($link);
hcclosedcomps($link);
echo "</div>";
hcimage($link,$comPk);
hcfooter();
?>
</div>
</body>
</html>

