<?php
echo '$_SERVER[PHP_SELF]: ' . basename(dirname(__FILE__))  . '<br />';
echo 'Dirname($_SERVER[PHP_SELF]: ' . dirname(__FILE__) . '<br>';
echo 'Dirname($_SERVER[PHP_SELF]: ' . $_SERVER['DOCUMENT_ROOT'] . '<br>';
?>