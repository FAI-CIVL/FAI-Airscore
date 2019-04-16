"""
Module for operations on tracks
Use:	import trackUtils
		pilPk = compUtils.get_track_pilot(filename)
		
Antonio Golfari - 2018
"""

# Use your utility module.
import myconn, calcUtils, kml

import sys, os, aerofiles, json
from datetime import date, time, datetime

class Track():
	"""
	A collection of functions to handle tracks.
	"""
	def __init__(self):
		pass

	def get_pilot(self, filename, test = 0):
		"""Get pilot associated to a track from its filename"""
		"""should be named as such: FAI.igc or LASTNAME_FIRSTNAME.igc"""
		message = ''
		fai = 0
		names = []
		pilPk = 0
	
		"""Get string"""
		fields = os.path.splitext(os.path.basename(filename))
		if fields[0].isdigit():
			"""check if string is FAI n."""
			fai = 0 + int(fields[0])
			message += ("file {} contains FAI n. {} \n".format(fields[0], fai))
		else:
			"""Gets name from string"""
			message += ("file {} contains pilot name {} \n".format(fields[0], fai))
			names = fields[0].replace('.', ' ').replace('_', ' ').split()

		"""Get pilot"""
		if fai > 0:
			"""Try to Get pilPk from FAI"""
			db = myconn.getConnection()
			query = ("SELECT pilPk FROM tblPilot WHERE pilFAI = {}".format(fai))
			message += ("Query: {}  \n".format(query))
			try:
				c = db.cursor()
				c.execute(query)
				row = c.fetchone()
			except Exception:
				message += ("Error while connecting to MySQL \n")
			else:
				if row is not None:
					pilPk = 0 + row['pilPk']
			finally:
				c.close()
		else:
			"""Try to Get pilPk from name"""
			cond = "', '".join(names)
			db = myconn.getConnection()
			query = ("""	SELECT 
								pilPk 
							FROM 
								tblPilot 
							WHERE 
								pilLastName IN ( '{0}' ) 
							AND 
								pilFirstName IN ( '{0}' )""".format(cond))
			message += ("Query: {}  \n".format(query))
			try:
				c = db.cursor()
				c.execute(query)
				row = c.fetchone()
			except Exception:
				message += ("Error while connecting to MySQL \n")
			else:
				if row is not None:
					pilPk = 0 + row['pilPk']
			finally:
				c.close()

		if pilPk == 0:
			"""No pilot infos in filename"""
			message += ("{} does NOT contain any valid pilot info \n".format(fields[0]))

		if test == 1:
			"""TEST MODE"""
			message += ("pilPk: {}  \n".format(pilPk))
			print (message)

		return pilPk

	def add_track(self, pilPk, tasPk, track, test):
		"""Imports track to db"""
		message = ''
		message += ("track {} will be imported for pilot with ID {} and task with ID {} \n".format(track, pilPk, tasPk))

		"""Get info on glider"""
		info = get_glider(pilPk, test)
		glider = info['glider']
		cert  = info['cert']

		"""read track file"""
		"""IGC, KML, OZI, LIVE"""
		result = track_reader(track, pilPk, test)

		"""creates a JSON data"""
		j = json.dumps(result, cls=DateTimeEncoder)

		"""writes a JSON file"""
		with open('json_data.json', 'wb') as fp:
			fp.write(j.encode("utf-8"))

		if test == 1:
			"""TEST MODE"""
			print (message)

		return result

	@staticmethod
	def filetype(self, track, test = 0):
		"""determine if igc / kml / live / ozi"""
		message = ''
		"""read first line of file"""
		with open(track) as f:
			first_line = f.readline()

		if first_line[:1] == 'A':
			"""IGC: AXCT7cea4d3ae0df42a1"""
			return "igc"
		elif first_line[:3] == '<?x': 
			"""KML: <?xml version="1.0" encoding="UTF-8"?>"""
			return "kml"
		elif first_line.contains("B  UTF"):
			return "ozi"
		elif first_line[:3] == 'LIV': 
			return "live"
		else:
			return None

	@staticmethod
	def is_flying(p1, p2, test = 0)
		"""check if pilot is flying between 2 gps points"""
		message = ''
		dist = quick_distance(p2, p1, test)
		altdif = abs(p2['gps_alt'] - p1['gps_alt'])
		timedif = time_diff(p2['time'], p1['time'], test)

	@staticmethod
	def track_reader(track, pilPk, test = 0):
		"""Reads track file and creates a dict() object"""
		message = ''
		type = Track.filetype(track, test)
		if type is not None:
			"""file is a valid track format"""
			message += ("File Type: {} \n".format(type))
			if type == "igc":
				"""using IGC reader from aerofile library"""
				with open(track, 'r', encoding='utf-8') as f:
					result = aerofiles.igc.Reader().read(f)
			if type == "kml":
				"""using KML reader created by Antonio Golfari"""
				with open(track, 'r', encoding='utf-8') as f:
					result = kml.Reader().read(f)

		else:
			Message += ("File {} (pilot ID {}) is NOT a valid track file. \n".format(track, pilPk))

		if test == 1:
			"""TEST MODE"""
			print (message)

		return result

def get_pil_result(pilPk, tasPk, test):
	"""Get pilot result in a given task"""
	message = ''
	traPk = 0
	db = myconn.getConnection()
	query = ("""	SELECT 
						T.traPk 
					FROM 
						tblTaskResult TR 
						JOIN tblTrack T USING (traPk) 
					WHERE 
						T.pilPk = {} 
						AND TR.tasPk = {} 
					LIMIT 
						1""".format(pilPk, tasPk))
	message += ("Query: {}  \n".format(query))
	try:
		c = db.cursor()
		c.execute(query)
		row = c.fetchone()
	except Exception:
		message += ("Error while connecting to MySQL \n")
	else:
		if row is not None:
			traPk = 0 + row['traPk']
	finally:
		c.close()	

	if pilPk == 0:
		"""No result found"""
		message += ("Pilot with ID {} has not been scored yet on task ID {} \n".format(pilPk, tasPk))

	if test == 1:
		"""TEST MODE"""
		message += ("traPk: {}  \n".format(traPk))
		print (message)

	return traPk
