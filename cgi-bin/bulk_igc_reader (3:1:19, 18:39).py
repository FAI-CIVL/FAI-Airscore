"""
Reads in a zip file full of .igc files
should be named as such: FAI.igc or LASTNAME_FIRSTNAME.igc
Use: python3 bulk_igc_reader.py [taskPk] [zipfile] [opt. test]

Antonio Golfari - 2018
"""
# Use your utility module.
import myconn
from compUtils import *
from trackUtils import *

import os, sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile, is_zipfile
from pathlib import Path
from os.path import isfile, basename

def printf(format, *args):
    sys.stdout.write(format % args)

def extract_tracks(file, dir, test = 0):
	message = ''
	error = 0
	"""Check if file exists"""
	if isfile(file):
		message += ('extracting: ' + file + ' in temp dir: ' + dir + ' \n')
		"""Create a ZipFile Object and load file in it"""
		with ZipFile(file, 'r') as zipObj:
			"""Extract all the contents of zip file in temporary directory"""
			zipObj.extractall(dir)
	else:
		message += ("reading error: {} does not exist or is not a zip file \n".format(file))
		error = 1

	if test == 1:
		"""TEST MODE"""
		print (message)

	return error

def get_tracks(dir, test = 0):
	"""Checks files and imports what appear to be tracks"""
	message = ''
	files = []

	message += ("Directory: {} \n".format(dir))
	message += ("Looking for files \n")

	"""check files in temporary directory, and get only tracks"""
	for file in os.listdir(dir):
		message += ("checking: {} \n".format(file))
		if ( (not (file.startswith(".") or file.startswith("_"))) and file.endswith(".igc") ):
			"""file is a valid track"""
			message += ("valid filename: {} \n".format(file))
			"""add file to tracks list"""
			files.append(os.path.join(dir, file))
		else:
			message +=  ("NOT valid filename: {} \n".format(file))

	message += ("files in directory: {} \n".format(len(os.listdir(dir))))
	message += ("files in list: {} \n".format(len(files)))
	for f in files:
		message += ("  {} \n".format(f))

	if test == 1:
		"""TEST MODE"""
		print (message)

	return files

def assign_tracks(tracks, test = 0):
	"""Find pilots to associate with tracks"""
	message = ''
	piltrk = dict()

	message += ("We have {} track to associate \n".format(len(tracks)))
	for file in tracks:
		filename = os.path.basename(file)
		pilPk = Track.get_pilot(filename, test)
		if pilPk > 0:
			message += ("pilot {} associated with track {} \n".format(pilPk, filename))
			piltrk[pilPk] = file
		else:
			message += ("Did NOT find a pilot for track {} \n".format(filename))
			
	for p, t in piltrk.items():
		message += ("  pil ID {} - track {} \n".format(p, t))

	if test == 1:
		"""TEST MODE"""
		print (message)

	return piltrk

def import_tracks(comPk, tasPk, piltrk, test = 0):
	"""Import tracks in db"""
	message = ''
	result = ''
	for pilPk, track in piltrk.items():
		"""Check if pilot is registered and if he has already a track"""
		if not is_registered(pilPk, comPk, test):
			"""pilot is not registered"""
			result += ("Pilot with ID {} is not registered yet in comp with ID {} \n".format(pilPk, comPk))
		elif get_pil_result(pilPk, tasPk, test):
			"""pilot has already been scored"""
			result += ("Pilot with ID {} has already a valid track for task with ID {} \n".format(pilPk, tasPk))
		else:
			"""pilot is registered and has no valid track yet"""
			result += Track.add(pilPk, tasPk, track, test)

	if test == 1:
		"""TEST MODE"""
		print (message)

	return result

def main():
	"""Main module"""
	test = 0
	"""check parameter is good."""
	if len(sys.argv) > 2:
		"""Get tasPk"""  
		tasPk = 0 + int(sys.argv[1])
		"""Get zip filename"""  
		zipfile = sys.argv[2]
		if len(sys.argv) > 3:
			"""Test Mode""" 
			print('Running in TEST MODE')
			test = 1

		"""Get comPk"""
		comPk = get_comp(tasPk, test)
		if comPk > 0:
			"""create a temporary directory"""
			with TemporaryDirectory() as tracksdir:
				error = extract_tracks(zipfile, tracksdir, test)
				if not error:
					"""find valid tracks"""
					tracks = get_tracks(tracksdir, test)
					"""associate tracks to pilots"""
					piltrk = assign_tracks(tracks, test)
					"""import tracks"""
					result = import_tracks(comPk, tasPk, piltrk, test)
				else:
					result = ("An error occured while dealing with file {} \n".format(zipfile))
		else:
			result = ("error: task ID {} does NOT belong to any Competition \n".format(tasPk))

	else:
		print('error: Use: python3 dbulk_igc_reader.py [taskPk] [zipfile] [opt. test]')

	print (result)

if __name__ == "__main__":
    main()
