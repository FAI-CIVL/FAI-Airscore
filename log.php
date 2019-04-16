<?php

  exec('tail /var/log/apache2/error.log', $error_logs);

  foreach($error_logs as $error_log) {

       echo "<br />".$error_log;
  }

 ?>

