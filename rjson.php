<?php
/*
Copyright (c) 2012, Dmytro V. Dogadailo. All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:
1. Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation and/or
other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/


/*
RJSON is Recursive JSON.

RJSON converts any JSON data collection into more compact recursive
form. Compressed data is still JSON and can be parsed with `JSON.parse`. RJSON
can compress not only homogeneous collections, but any data sets with free
structure.

RJSON is stream single-pass compressor, it extracts data schemes from a
document, assign each schema unique number and use this number instead of
repeating same property names again and again.

Bellow you can see same document in both forms.

JSON:

{
    "id": 7,
    "tags": ["programming", "javascript"],
    "users": [
    {"first": "Homer", "last": "Simpson"},
    {"first": "Hank", "last": "Hill"},
    {"first": "Peter", "last": "Griffin"}
    ],
    "books": [
    {"title": "JavaScript", "author": "Flanagan", "year": 2006},
    {"title": "Cascading Style Sheets", "author": "Meyer", "year": 2004}
    ]
}

RJSON:

{
    "id": 7,
    "tags": ["programming", "javascript"],
    "users": [
    {"first": "Homer", "last": "Simpson"},
        [2, "Hank", "Hill", "Peter", "Griffin"]
    ],
    "books": [
    {"title": "JavaScript", "author": "Flanagan", "year": 2006},
        [3, "Cascading Style Sheets", "Meyer", 2004]
    ]
}

RJSON allows to:

* reduce JSON data size and network traffic when gzip isn't available. For
example, in-browser 3D-modeling tools like [Mydeco
3D-planner](http://mydeco.com/3d-planner/) may process and send to server
megabytes of JSON-data;
* analyze large collections of JSON-data without
unpacking of whole dataset. RJSON-data is still JSON-data, so it can be
traversed and analyzed after parsing and fully unpacked only if a document meets
some conditions.

*/


/**
 * @param {*} Any valid for JSON javascript data.
 * @return {*} Packed javascript data, usually a dictionary.
 */

function is_assoc($array) 
{
    return (bool)count(array_filter(array_keys($array), 'is_string'));
}

function is_encoded($arr) 
{
    if (is_array($arr) && array_key_exists(0, $arr) && is_numeric($arr[0]) && ($arr[0] != 0)) return true;
    return false;
}

function rjson_pack($data) 
{
    // encoded, i, j, k, v, current, last, len, schema, schemaKeys, schemaIndex;
    $maxSchemaIndex = 0;
    $schemas = array();

    $encode = function($value) use(&$schemas, &$maxSchemaIndex, &$encode)
    {
        if (!is_array($value))
        {
            // non-objects or null return as is
            return $value;
        }
    
        if (!is_assoc($value)) 
        {
            $len = sizeof($value);
            if ($len == 0) 
            {
                return array();
            }
    
            $encoded = array();
            if (is_numeric($value[0])) 
            {
                $encoded[] = 0;  // 0 is schema index for Array
            }
    
            for ($i = 0; $i < $len; $i++) 
            {
                $v = $value[$i];
                $current = $encode($v);
                if ($i > 0)
                {
                    $last = $encoded[sizeof($encoded) - 1];
                }
                if (is_encoded($current) && is_array($last) && ($current[0] == $last[0])) 
                {
                    // current and previous object have same schema,
                    // so merge their values into one array
                    $encoded[sizeof($encoded) - 1] = array_merge($last, $current);
                }
                else 
                {
                    $encoded[] = $current;
                }
            }
        }
        else 
        {
            if (sizeof($value) == 0) 
            {
                return array();
            }
    
            $schemaKeys = array_keys($value); //getKeys(value).sort();
    
            $schema = sizeof($schemaKeys) + ':' + implode('|', $schemaKeys);
            if (array_key_exists($schema, $schemas))
            {
                // known schema
                $schemaIndex = $schemas[$schema];
                $encoded = array($schemaIndex);
                foreach ($schemaKeys as $k)
                {
                    $encoded[] = $encode($value[$k]);
                }
            }
            else 
            {    
                // new schema
                $schemas[$schema] = ++$maxSchemaIndex;
                $encoded = array();
                foreach ($schemaKeys as $k) 
                {
                    $encoded[$k] = $encode($value[$k]);
                }
            }
        }
    
        print "SCHEMA ". var_dump($schemas);
        return $encoded;
    };

    $res = $encode($data);

    return json_encode($res);
}


/**
 * @param {*} data Packed javascript data.
 * @return {*} Original data.
 */
function rjson_unpack($value) 
{

    $maxSchemaIndex = 0;
    $schemas = array();

    if (!$value || !is_array($value))
    {
        // non-objects or null return as is
        return $value;
    }

    if (!is_assoc($value)) 
    {
        $len = sizeof($value);
        if ($len == 0) 
        {
            $decoded = array();
        } 
        else if ($value[0] === 0 || !is_numeric($value[0]))
        {
            // decode array of something
            $decoded = array(); 
            for ($i = ($value[0] === 0 ? 1 : 0); $i < $len; $i++) 
            {
                $v = $value[$i];
                $obj = rjson_unpack($v);
                if (is_encoded($v) && !is_assoc($obj))
                {
                    // several objects was encoded into single array
                    // FIX: $decoded = array_combine(XXX,$obj);
                    //$decoded = decoded.concat(obj);
                } 
                else 
                {
                    $decoded[] = $obj;
                }
            }
        } 
        else 
        {
            $schemaKeys = $schemas[$value[0]];
            $schemaLen = sizeof($schemaKeys);
            $total = (sizeof($value) - 1) / $schemaLen;
            if ($total > 1) 
            {
                $decoded = array(); // array of objects with same schema
                for ($i = 0; $i < $total; $i++) 
                {
                    $obj = array();
                    foreach ($schemaKeys as $k)
                    {
                        $obj[$k] = rjson_unpack($value[$i * $schemaLen + $j]);
                    }
                    $decoded[] = $obj;
                }
            } 
            else 
            {
                $decoded = array();
                foreach ($schemaKeys as $k)
                {
                    $decoded[$k] = rjson_unpack($value[$j]);
                }
            }
        }

    } 
    else 
    { 
        // new schema
        $schemaKeys = array_keys($value);
        if (sizeof($schemaKeys) == 0) 
        {
            return array();
        }
        $schemas[++$maxSchemaIndex] = $schemaKeys;
        $decoded = array();
        foreach ($schemaKeys as $k)
        {
            $decoded[$k] = rjson_unpack($value[$k]);
        }
    }

    return $decoded;
    //return json_decode($decoded);
}


$tst = array(
    "id" => 7,
    "tags" => array("programming", "javascript"),
    "users" => array(
    array("first" => "Homer", "last" => "Simpson"),
    array("first" => "Hank", "last" => "Hill"),
    array("first" => "Peter", "last" => "Griffin")
    ),
    "books" => array(
    array("title" => "JavaScript", "author" => "Flanagan", "year" => 2006),
    array("title" => "Cascading Style Sheets", "author" => "Meyer", "year" => 2004)
    )
);

$tstenc = rjson_pack($tst);
print var_dump($tstenc);



?>
