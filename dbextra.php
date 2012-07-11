<?php
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

function insertup($link,$table,$key,$clause,$map)
{
    $keys = array_keys($map);

    if ($clause != '')
    {
        $sql = "select * from $table where $clause";
        $result = mysql_query($sql,$link) 
            or die ("insertup (select): $table ($clause) query failed: " . mysql_error());
        $nrows = mysql_num_rows($result);
    }

    $keystr = array();
    if ($nrows > 0)
    {
        $ref = mysql_fetch_array($result);

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
        $result = mysql_query($sql,$link) 
            or die ("insertup (update): $table ($clause) query failed: " . mysql_error());
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
        $result = mysql_query($sql,$link) 
            or die ("insertup (insert): $table ($clause) query failed: " . mysql_error());
        return mysql_insert_id($link);
    }
}
?>
