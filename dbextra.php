<?php

//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//

function esc($val)
{
    return mysql_real_escape_string($val);
}
function quote($val)
{
    if (is_numeric($val))
    {
        return $val;
    }
    else
    {
        return "'$val'";
    }
}

function insertnullup($link,$table,$key,$clause,$map)
{
    $keys = array_keys($map);

    if ($clause != '')
    {
        $sql = "select * from $table where $clause";
//        $result = mysql_query($sql,$link) or die ("insertup (select): $table ($clause) query failed: " . mysql_error());
        $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' insertup (select): $table ($clause) query failed: ' . mysqli_connect_error());
//        $nrows = mysql_num_rows($result);
		$nrows = mysqli_num_rows($result);
    }

    $keystr = [];
    if ($nrows > 0)
    {
//        $ref = mysql_fetch_array($result, MYSQL_ASSOC);
	$ref = mysqli_fetch_assoc($result);

        // update fields
        foreach ($map as $k => $val)
        {
            if ($map[$k] != '')
            {
                $ref[$k] = $val;
            }

            // only update null fields
            if ($ref[$k] == 'null')
            {
                array_push($keystr, $k . "=" . quote($ref[$k]));
            }
        }

        # create nice string
        if (sizeof($keystr) > 0)
        {
            $fields = join(",", $keystr);
            $sql = "update $table set $fields where $clause";
            // echo $sql . "<br>";
//            $result = mysql_query($sql,$link) or die ("insertnullup (update): $table ($clause) query failed: " . mysql_error());
        	$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' insertnullup (update): $table ($clause) query failed: ' . mysqli_connect_error());
        }
        return $ref[$key];
    }
    else
    {
        // else insert
        $fields = join(',', $keys);
        foreach ($map as $k => $val)
        {
            $map[$k] = quote($val);
        }
        $values = array_values($map);
        $valstr = join(',', $values);
        $sql = "INSERT INTO $table ($fields) VALUES ($valstr)";
        # get last key insert for primary key value ..
        //echo $sql . "<br>";
//        $result = mysql_query($sql,$link) or die ("insertnullup (insert): $table ($clause) query failed: " . mysql_error());
    	$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' insertnullup (update): $table ($clause) query failed: ' . mysqli_connect_error());
//        return mysql_insert_id($link);
		return mysqli_insert_id($link);
    }
}

function insertup($link,$table,$key,$clause,$map)
{
    $keys = array_keys($map);

    if ($clause != '')
    {
        $sql = "select * from $table where $clause";
//        $result = mysql_query($sql,$link) or die ("insertup (select): $table ($clause) query failed: " . mysql_error());
//        $nrows = mysql_num_rows($result);
        $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' insertup (select): $table ($clause) query failed: ' . mysqli_connect_error());
		$nrows = mysqli_num_rows($result);

    }

    $keystr = [];
    if ($nrows > 0)
    {
//        $ref = mysql_fetch_array($result, MYSQL_ASSOC);
		$ref = mysqli_fetch_assoc($result);

        // update fields
        foreach ($map as $k => $val)
        {
            if ($map[$k] != '')
            {
                $ref[$k] = $val;
            }

            array_push($keystr, $k . "=" . quote($ref[$k]));
        }

        # create nice string
        $fields = join(",", $keystr);
        $sql = "update $table set $fields where $clause";
        //echo $sql . "<br>";
//        $result = mysql_query($sql,$link) or die ("insertup (update): $table ($clause) query failed: " . mysql_error());
        $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' insertup (select): $table ($clause) query failed: ' . mysqli_connect_error());
        return $ref[$key];
    }
    else
    {
        // else insert
        $fields = join(',', $keys);
        foreach ($map as $k => $val)
        {
            $map[$k] = quote($val);
        }
        $values = array_values($map);
        $valstr = join(',', $values);
        $sql = "INSERT INTO $table ($fields) VALUES ($valstr)";
        # get last key insert for primary key value ..
        // echo $sql . "<br>";
//        $result = mysql_query($sql,$link) or die ("insertup (insert): $table ($clause) query failed: " . mysql_error());
//        return mysql_insert_id($link);
        $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' insertup (select): $table ($clause) query failed: ' . mysqli_connect_error());
		return mysqli_insert_id($link);
    }
}
?>
