<?php 
if (isset($_REQUEST["data"])){
	$f=fopen("data-from-pi.txt", "a+");
	$data_raw_in = json_decode($_REQUEST["data"]);
	$jsonarray = array();
	foreach ($data_raw_in as $k => $v){
		array_push($jsonarray, $k);
		fwrite($f, "$k, $v\n");
	}
	echo json_encode($jsonarray);
}else{
	echo "can't get data";
}
?>
