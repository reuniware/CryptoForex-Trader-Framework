<?php

    $btcusdt_bid = 0;
    $btcusdt_ask = 0;

    $context = stream_context_create(array(
        'http' => array('ignore_errors' => true, 'proxy' => '213.52.102.43:10800', 'timeout' => 2), // Norvège proxy
    ));
    
    try {
        // $json = file_get_contents("https://api.binance.com/api/v3/ticker/bookTicker?symbol=BTCUSDT", false, $context);
        // $obj = json_decode($json);
        
        // //var_dump($obj);
        
        // $btcusdt_bid = $obj->bidPrice;
        // $btcusdt_ask = $obj->askPrice;
        // $btcusdt_bid = number_format($btcusdt_bid, 2, '.', '');
        // $btcusdt_ask = number_format($btcusdt_ask, 2, '.', '');
        // //$btcusd_bid = $bid;
        // //$btcusd_ask = $ask;
    } catch (Exception $e) {
        echo 'Proxy must be changed<br/>';
    }

    
//     exit;
// }
    
if (!isset($_GET['static'])) {
    header("refresh: 10");
    echo "Auto-refresh is ON : Every 10 seconds<br/>";
}

define("MYSQL_SERVER", "localhost");
define("MYSQL_USER", "id20856516_eurodollarbot");
define("MYSQL_PASSWORD", "");
define("MYSQL_DB", "id20856516_eurodollarbot");
define("TBL_PREFIX", "eurodollarbot");
define("CREATE_DB_IF_NOT_EXISTS", true);
define("CREATE_TABLES_IF_NOT_EXIST", true);
define("LOG_IP", true);
define("LOG_IP_IGNORE", "127.0.0.1");
define("DISABLE_DETAILED_LOG_VIEW", true);
define("DEBUG", true);
define("SHOW_ONLY_TODAY", true);

//echo basename($_SERVER['PHP_SELF']);

// LOG IP si paramètre LOG_IP = true
if (LOG_IP==true){
    $db = new mysqli(MYSQL_SERVER, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB);
    if ($db->connect_errno) {
        exit;
    }
    $client_ip = $_SERVER['REMOTE_ADDR'];
    $nslookup = gethostbyaddr($client_ip);
    $url = $_SERVER['PHP_SELF'];
    $r = mysqli_query($db, "SELECT * FROM " . TBL_PREFIX . "_ip_address_log where ip_address = '" . $client_ip . "'");
    if ($r->num_rows > 0) {
        if($row = $r->fetch_assoc()) {
            $count = $row["count"];
            $r = mysqli_query($db, "update " . TBL_PREFIX . "_ip_address_log set access_date_time = NOW(), count = " . ($count+1) . ", nslookup='" . $nslookup . "', url='" . $url . "' where ip_address = '" . $client_ip . "'");
        }
    } else {
        $r = mysqli_query($db, "insert into " . TBL_PREFIX . "_ip_address_log(ip_address, access_date_time, nslookup, url, count) values ('" . $client_ip . "',NOW(),'" . $nslookup . "','" . $url . "',1)");
    }
    $r = mysqli_query($db, "DELETE FROM " . TBL_PREFIX . "_ip_address_log where ip_address like '%" . LOG_IP_IGNORE . "%'");

    $result = mysqli_query($db, 'SELECT SUM(count) AS value_sum FROM ' . TBL_PREFIX . "_ip_address_log"); 
    $row = mysqli_fetch_assoc($result); 
    $sum = $row["value_sum"];
    echo "<h1 style='font-size: 12;'>This page has been printed " . $sum . " times</h1>";

    $db->close();
}



if (isset($_GET['view_logs'])) {
    echo "<html><head><style> table { width:100%; } table, th, td { border: 1px solid gray; border-collapse: collapse; } th, td { padding: 5px; text-align: left; } table#t01 tr:nth-child(even) { background-color: #eee; } table#t01 tr:nth-child(odd) { background-color:#fff; } table#t01 th { background-color: black; color: white; } </style><title>Ichimoku Scanner</title></head><body  style='font-family:arial; color: #ffffff; background-color: #000000'>";
    echo "<img src='ichimokuscannerlogo.PNG' alt='Ichimoku Scanner Logo'>";
    echo "<h3>Logs</h3><a href='http://ichimoku-expert.blogspot.com'>ichimoku-expert.blogspot.com</a><br/>";
    echo "<br/>";
    $db = new mysqli(MYSQL_SERVER, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB);
    if ($db->connect_errno) {
        exit;
    }
    $r = mysqli_query($db, "SELECT * FROM " . TBL_PREFIX . "_ip_address_log order by access_date_time desc");
    if ($r->num_rows > 0) {
        echo "<table>";
        while($row = $r->fetch_assoc()) {
            echo "<tr>";
            $access_date_time = $row["access_date_time"];
            $ip_address = $row["ip_address"];
            $nslookup = $row["nslookup"];
            $url = $row["url"];
            $count = $row["count"];
            if (!DISABLE_DETAILED_LOG_VIEW){
                echo "<td>" . $access_date_time . "</td><td>" . $ip_address . "</td><td>" . $nslookup . "</td><td>"  . $url . "</td><td>" . $count . "</td>";
            } else {
                echo "<td>" . $access_date_time . "</td><td> DISABLED </td><td> DISABLED </td><td>"  . $url . "</td><td>" . $count . "</td>";
            }
            echo "</tr>";
        }
        echo "</table>";
    }
    $db->close();
    echo "</body></html>";
    exit;
}
$arrOptions=array(
    "ssl"=>array(
        "verify_peer"=>false,
        "verify_peer_name"=>false,
    ),
);

 $page = file_get_contents("https://rates.fxcm.com/RatesXML", false, stream_context_create($arrOptions));
 $xml = new SimpleXMLElement($page);
 $result = $xml->xpath('/Rates/Rate');
// echo 'result count = ' . count($result);
// echo '<br/>' . 'Live FXCM rates' . '<br/>';                 
// //$rates=array();
$eurusd_bid = 0;
$eurusd_ask = 0;
 for($i=0;$i<count($result);$i++){
     $symbol = (string) $result[$i]->xpath('@Symbol')[0];
     $bid = (string) $result[$i]->xpath('Bid')[0]; // sell price
     $ask = (string) $result[$i]->xpath('Ask')[0]; // buy price
     $rates[$i]["symbol"]=$symbol;
     $rates[$i]["bid"]=$bid;
     $rates[$i]["ask"]=$ask;

//     //echo $rates[$i][$symbol];
     //echo $symbol . ' ' . $bid . '<br/>';
     if ($symbol == 'EURUSD') {
        //echo $symbol . ' BID(VENDRE)=' . $bid . ' ASK(ACHETER)=' . $ask .  '<br/><br/>';
        echo "<h1 style='font-size: 12;'>" . $symbol . ' (FXCM) BID(VENDRE)=' . $bid . ' ASK(ACHETER)=' . $ask . "</h1>";
        $eurusd_bid = $bid;
        $eurusd_ask = $ask;
     } else if ($symbol == 'EURGBP') {
        //echo $symbol . ' BID(VENDRE)=' . $bid . ' ASK(ACHETER)=' . $ask .  '<br/><br/>';
        echo "<h1 style='font-size: 12;'>" . $symbol . ' (FXCM) BID(VENDRE)=' . $bid . ' ASK(ACHETER)=' . $ask . "</h1>";
        $eurgbp_bid = $bid;
        $eurgbp_ask = $ask;		 
	 } else if ($symbol == 'BTCUSD') {
        echo "<h1 style='font-size: 12;'>" . $symbol . ' (FXCM) BID(VENDRE)=' . $bid . ' ASK(ACHETER)=' . $ask . "</h1>";
        $btcusd_bid = $bid;
        $btcusd_ask = $ask; // ne fonctionne pas le week-end (pas mis à jour à priori)
     }
 }
echo "<h1 style='font-size: 12;'>" . 'BTCUSDT (BINANCE)' . ' BID(VENDRE)=' . $btcusdt_bid . ' ASK(ACHETER)=' . $btcusdt_ask . "</h1>";

 
// $title = "";




$db = new mysqli(MYSQL_SERVER, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB);
if ($db->connect_errno) {
    echo "Erreur : " . $db->connect_errno . " <br/>";
    exit;
}

if (isset($_GET['drop_tables11121975'])) {
    $db = new mysqli(MYSQL_SERVER, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB);
    if ($db->connect_errno) {
        exit;
    } 
    
    //$sql = "DROP TABLE " . TBL_PREFIX . "_notification IF EXISTS;";
    //$r = mysqli_query($db, $sql);    

    $sql = $db->prepare("DROP TABLE " . TBL_PREFIX . "_notification"); 
    $sql->execute();

    $db->close();
}

if (isset($_GET['create_tables11121975'])) {
    //echo "create db";
    $db = new mysqli(MYSQL_SERVER, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB);
    if ($db->connect_errno) {
        exit;
    }
    $sql = "CREATE TABLE " . TBL_PREFIX . "_notification (`timestamp` text COLLATE utf8_unicode_ci NOT NULL, `asset` text COLLATE utf8_unicode_ci NOT NULL, predicted_diff float, predicted_value float, bid float, ask float ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;";
    $r = mysqli_query($db, $sql);
    $sql = "CREATE TABLE " . TBL_PREFIX . "_ip_address_log (`id` bigint(20) NOT NULL AUTO_INCREMENT, `access_date_time` datetime NOT NULL, `ip_address` varchar(32) COLLATE latin1_general_ci NOT NULL, `nslookup` text, `url` varchar(255) COLLATE latin1_general_ci DEFAULT NULL, `count` bigint(20), PRIMARY KEY (`id`)) ENGINE=MyISAM  DEFAULT CHARSET=latin1 COLLATE=latin1_general_ci";
    $r = mysqli_query($db, $sql);
    // $sql = "CREATE TABLE " . TBL_PREFIX . "_ssb_alert (`timestamp` text COLLATE utf8_unicode_ci NOT NULL, `period` text COLLATE utf8_unicode_ci NOT NULL, `name` text COLLATE utf8_unicode_ci NOT NULL, `type` text COLLATE utf8_unicode_ci NOT NULL, `price` double NOT NULL, `ssb` double NOT NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;";
    // $r = mysqli_query($db, $sql);
    // $sql = "CREATE TABLE " . TBL_PREFIX . "_ip_address_log (`id` bigint(20) NOT NULL AUTO_INCREMENT, `access_date_time` datetime NOT NULL, `ip_address` varchar(32) COLLATE latin1_general_ci NOT NULL, `nslookup` text, `url` varchar(255) COLLATE latin1_general_ci DEFAULT NULL, `count` bigint(20), PRIMARY KEY (`id`)) ENGINE=MyISAM  DEFAULT CHARSET=latin1 COLLATE=latin1_general_ci";
    // $r = mysqli_query($db, $sql);
    // $sql = "CREATE TABLE " . TBL_PREFIX . "_2jcs_alert (`id` bigint(20) NOT NULL, `timestamp` text COLLATE utf8_unicode_ci NOT NULL, `period` text COLLATE utf8_unicode_ci NOT NULL, `symbol` text COLLATE utf8_unicode_ci NOT NULL, `buy` double NOT NULL,`sell` double NOT NULL, `h1_ls_validated` text COLLATE utf8_unicode_ci NOT NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;";
    // $r = mysqli_query($db, $sql);
    // $sql = "ALTER TABLE " . TBL_PREFIX . "_2jcs_alert ADD PRIMARY KEY (`id`);";
    // $r = mysqli_query($db, $sql);
    // $sql = "ALTER TABLE " . TBL_PREFIX . "_2jcs_alert MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;";
    // $r = mysqli_query($db, $sql);
    // $sql= "ALTER TABLE " . TBL_PREFIX . "_2jcs_alert ADD `m1_ls_validated` TEXT NOT NULL  AFTER `h1_ls_validated`";
    // $r = mysqli_query($db, $sql);
    // $sql="CREATE TABLE " . TBL_PREFIX . "_history (`id` bigint(20) NOT NULL,`timestamp` text COLLATE utf8_unicode_ci NOT NULL,`symbol` text COLLATE utf8_unicode_ci NOT NULL,`buy` double NOT NULL,`sell` double NOT NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;";
    // $r = mysqli_query($db, $sql);
    // $sql="ALTER TABLE " . TBL_PREFIX . "_history ADD PRIMARY KEY (`id`);";
    // $r = mysqli_query($db, $sql);
    // $sql="ALTER TABLE " . TBL_PREFIX . "_history MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;";
    // $r = mysqli_query($db, $sql);
    $db->close();
}

if (isset($_GET['upload_history'])) {
    $history = $_GET['upload_history'];
    echo "received=  [[$history]]<br/>";
    $array = explode(";", $history);
    if (count($array)==4){
        $timestamp = $array[0];
        $asset = $array[1];
        $predicted_diff = $array[2];
        $predicted_value = $array[3];
        $db = new mysqli(MYSQL_SERVER, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB);
        if ($db->connect_errno) {
            echo "Error : " . $db->connect_errno . " <br/>";
            exit;
        }
        if ($asset == 'EUR/USD') {
            //$timestamp = (new DateTime())->format('Y-m-d H:i:s');
            $r = mysqli_query($db, "insert into " . TBL_PREFIX . "_notification(timestamp, asset, predicted_diff, predicted_value, bid, ask) values ('" . $timestamp . "', '" . $asset . "','" . $predicted_diff . "','" . $predicted_value . "','" . $eurusd_bid . "','" . $eurusd_ask . "')");
            echo 'History recorded OK.<br/>';
        } else if ($asset == 'EUR/GBP') {
            //$timestamp = (new DateTime())->format('Y-m-d H:i:s');
            $r = mysqli_query($db, "insert into " . TBL_PREFIX . "_notification(timestamp, asset, predicted_diff, predicted_value, bid, ask) values ('" . $timestamp . "', '" . $asset . "','" . $predicted_diff . "','" . $predicted_value . "','" . $eurgbp_bid . "','" . $eurgbp_ask . "')");
            echo 'History recorded OK.<br/>';		}
		else if ($asset == 'BTC/USDT') {
            //$timestamp = (new DateTime())->format('Y-m-d H:i:s');
            $r = mysqli_query($db, "insert into " . TBL_PREFIX . "_notification(timestamp, asset, predicted_diff, predicted_value, bid, ask) values ('" . $timestamp . "', '" . $asset . "','" . $predicted_diff . "','" . $predicted_value . "','" . $btcusd_bid . "','" . $btcusd_ask . "')");
            echo 'History recorded OK.<br/>';            
        }
        
        $db->close();
        exit;
    }
}

$db = new mysqli(MYSQL_SERVER, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB);
if ($db->connect_errno) {
    exit;
}

echo("<style>");
echo "html * {";
echo "  font-size: 16px;";
echo "  line-height: 1.625;";
echo "  color: #2020131;";
echo "  font-family: Nunito, serif;";
echo "}";
echo "table, th, td {";
echo "  border: 1px solid black;";
/*echo "   padding: 15px;";
echo "   padding-top: 2px;";
echo "   padding-bottom: 2px;";
echo "   padding-left: 10px;";
echo "   padding-right: 10px;";
echo "   tr:nth-child(even) {";
echo "      background-color: #D6EEEE;";*/
echo "   }";
echo "table {";
echo "  border-collapse: collapse;";
echo "  border: 1px solid black;";

//echo "  width: 100%;";
echo "}";
echo "th, td {";
echo "  text-align: left;";
echo "  padding: 8px;";
echo "}";
echo "tr:nth-child(even) {";
echo "  background-color: #D5DBDB;";
echo "}";
echo "</style>";
//echo "echo "}";

echo("</style>");

echo "<img src='https://pbs.twimg.com/profile_banners/905696024504750080/1685961450/1500x500' width=50% height=25%/><br/>";

//echo "<h3><a href='https://discord.gg/XydQH6Zz'>Discord Group : Click here to join</a></h3>";
echo "<h3><a href='https://eurodollarbot.000webhostapp.com/?static'>Static version : Click here to view</a>&nbsp&nbsp&nbsp&nbsp<a href='https://eurodollarbot.000webhostapp.com/'>Auto-refresh version : Click here to view</a></h3>";


//echo "TIMESTAMP;ASSET;PREDICTED_DIFF;PREDICTED_VALUE(YF);BID;ASK;DIFF_BID;DIFF_ASK<br/>";

echo "<h3>Predictions can be effective in the following minutes/hours (up to 4 hours and sometimes more).</h3>";

//echo "<h2><font color='green'>MESSAGE FROM ADMIN : Investors wanted, my email is InvestDataSystems@Yahoo.Com</font></h2>";

$asset_filter = "EUR/USD";
if (isset($_GET['asset'])) {
    $asset_filter = strtoupper($_GET['asset']);
    if (strlen($asset_filter) > 32) {
        $asset_filter = "EUR/USD";
    } else {
        if ($asset_filter == "EURUSD") {
            $asset_filter = "EUR/USD";
        } else if ($asset_filter == "EURGBP") {
			$asset_filter = "EUR/GBP";
		} else if ($asset_filter == "BTCUSDT") {
            $asset_filter = "BTC/USDT";
        } else {
            $asset_filter = "EUR/USD";
        }
    }
}

if (isset($_GET['all'])) {
    $asset_filter = '%';
    $z = mysqli_query($db, "select * from " . TBL_PREFIX . "_notification where asset like '" . $asset_filter . "' order by timestamp desc");
} else {
    $z = mysqli_query($db, "select * from " . TBL_PREFIX . "_notification WHERE asset like '" . $asset_filter . "' AND INSTR(timestamp, DATE_FORMAT(NOW(), '%Y-%m-%d')) > 0 order by timestamp desc");    
}

if (isset($_GET['date'])) {
	$date = $_GET['date'];
	if (strlen($date) == 10) {
		$request = "select * from " . TBL_PREFIX . "_notification WHERE INSTR(timestamp, '" . $date . "') > 0 order by timestamp desc";
		//echo "request = " . $request;
		$z = mysqli_query($db, "select * from " . TBL_PREFIX . "_notification WHERE INSTR(timestamp, '" . $date . "') > 0 order by timestamp desc");    
	}		
}

echo "<table>";

echo "<tr>";
echo "<th>TIMESTAMP</th>";
echo "<th>ASSET</th>";
echo "<th>PREDICTED<br/>DIFF</th>";
if ($asset_filter == 'EUR/USD') {
    echo "<th>PREDICTED<br/>VALUE(YF)</th>";
} else if ($asset_filter == 'BTC/USDT') {
    echo "<th>PREDICTED<br/>VALUE(BIN)</th>";
} else if ($asset_filter == '%') {
    echo "<th>PREDICTED<br/>VALUE</th>";
}
echo "<th>BID AT<br/>PREDICTION</th>";
echo "<th>ASK AT<br/>PREDICTION</th>";
echo "<th>CURRENT<br/>DIFF BID</th>";
echo "<th>CURRENT<br/>DIFF ASK</th>";
echo "</tr>";


while($row = $z->fetch_assoc()) {              
    $timestamp = $row["timestamp"];
    $asset = $row["asset"];
    $predicted_diff = $row["predicted_diff"];
    $predicted_value = $row["predicted_value"];
    $bid = $row["bid"];
    $ask = $row["ask"];
    
    $nb_decimals = 5;

    if ($asset == "EUR/USD") {
        $diff_bid = $eurusd_bid - $bid; // prix en cours - prix au moment de l'alerte
        $diff_ask = $eurusd_ask - $ask;
        $nb_decimals = 5;
    } else if ($asset == "EUR/GBP") {
        $diff_bid = $eurgbp_bid - $bid; // prix en cours - prix au moment de l'alerte
        $diff_ask = $eurgbp_ask - $ask;
        $nb_decimals = 5;
	}		
	else if ($asset == "BTC/USDT") {
        $diff_bid = $btcusdt_bid - $bid; // prix en cours - prix au moment de l'alerte
        $diff_ask = $btcusdt_ask - $ask;
        $nb_decimals = 0;
    }

    if ($diff_bid < 0) {
        $diff_bid = "<b><font color='red'>" . number_format($diff_bid, $nb_decimals, '.', '') . "</font></b>";
    } else {
        $diff_bid = "<b><font color='green'>" . number_format($diff_bid, $nb_decimals, '.', '') . "</font></b>";
    }

    if ($diff_ask < 0) {
        $diff_ask = "<b><font color='red'>" . number_format($diff_ask, $nb_decimals, '.', '') . "</font></b>";
    } else {
        $diff_ask = "<b><font color='green'>" . number_format($diff_ask, $nb_decimals, '.', '') . "</font></b>";
    }
    
    if ($predicted_diff > 0)
    {
        $predicted_diff = "<b><font color='green'>" . $predicted_diff . "</font></b>";
    } else {
        $predicted_diff = "<b><font color='red'>" . $predicted_diff . "</font></b>";
    }
    
    $bid = number_format($bid, $nb_decimals, '.', '');
    $ask = number_format($ask, $nb_decimals, '.', '');
    
    echo "<tr>";

    //echo $timestamp . ";" . $asset . ";" . $predicted_diff . ";" . $predicted_value . ";" . $bid . ";" . $ask . ";" .  $diff_bid . ";" . $diff_ask . "<br/>";

    echo "<td>" . $timestamp . "</td><td>" . $asset . "</td><td>" . $predicted_diff . "</td><td>" . $predicted_value . "</td><td>" . $bid . "</td><td>" . $ask . "</td><td>" .  $diff_bid . "</td><td>" . $diff_ask . "</td>";

    echo "</tr>";

}
//fclose($handle);
$db->close();

echo "</table>";



?>
