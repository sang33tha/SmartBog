import time
import requests
import json
import MySQLdb
def main():
	database_connection = None
	while True:
		try:
			database_connection = MySQLdb.connect(host='localhost', user='user', passwd='123456', db='data_sync')
			cur = database_connection.cursor()
			cur.execute("select `id`, `content`, `timestamp` from `serial_data` where `flag` = 0 limit 0, 20;")
			all_results = cur.fetchall()
			result_to_send = {}
			for r in all_results:
				if r[0] is not None and r[1] is not None:
					result_to_send[r[0]] = "[" + str(r[2]) + "]" + r[1]
			request = requests.post("http://159.203.78.94/weather/smart_bog_receiver.php", data={"data": str(json.dumps(result_to_send))})
			if request.status_code == 200:
				response_json_array = json.loads(request.text)
				for success_id in response_json_array:
					cur.execute("delete from `serial_data` where `id` = %s", [success_id])
		except:
			pass
		time.sleep(1)
main()

