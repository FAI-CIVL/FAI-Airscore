"""
Reads in a CSV membership list
Use: python3 bulk_pilot_import.py [csv file name] [opt. test]

Antonio Golfari - 2018
"""

# Use your utility module.
import myconn

import sys, csv, os.path
from pathlib import Path

def read_membership(file,test):

	message = ''
	"""Check if file exists"""
	my_file = Path(file)
	if not my_file.is_file():
		print ('reading error: ' + file + ' does not exist')
	else:
		if test == 1:
			message += ('reading: ' + file + ' \n')
		"""Read CSV File"""
		with open(file) as csv_file:
			csv_reader = csv.reader(csv_file, delimiter=',')
			line_count = 0
			for row in csv_reader:
				pilFAI = row[0]
				pilFName = row[1]
				pilLName = row[2]
				pilSex = row[4]
				nat = row[3]
				if test == 1:
					message += ('-- new line -- \n')
					message += ('pilot ' + pilLName + ' ' + pilFName + ', from ' + nat + ', ' + pilSex + ', n. ' + pilFAI + '\n')

				"""Get Nat code"""
				try:
					db = myconn.getConnection()
					c = db.cursor()
					c.execute("SELECT C.natID AS Code FROM tblCountryCodes C WHERE C.natIso3 = '{}' LIMIT 1".format(nat))
					pilNat = 0 + c.fetchone()['Code']
					#print('nat: ' + nat + ' , code = ' + format(pilNat))
				except ImportError:
					print ("Error while connecting to MySQL")
				finally:
					db.close()

				"""default nat to Italy"""
				if not str(pilNat).isdigit():
					pilNat = 380

				try:
					db = myconn.getConnection()
					c = db.cursor()
					"""Check if pilot exists in pilots main table"""
					c.execute("SELECT pilPK AS ID FROM tblPilot WHERE (pilLastName LIKE '%{}%' AND pilFirstName LIKE '%{}%') OR (pilLastName LIKE '%{}%' AND pilFAI = {}) LIMIT 1".format(pilLName, pilFName, pilLName, pilFAI))
					if not c.rowcount == 0:
						"""Pilot exists already"""
						pil = 0 + c.fetchone()['ID']
						message += ("pilot {} {} exists in pilots list: id {} \n".format(pilLName, pilFName, pil))
					else:
						"""Check if FAI exists"""
						c.execute("SELECT pilPK AS ID, pilLastName AS Name FROM tblExtPilot WHERE pilFAI = '{}' LIMIT 1".format(pilFAI))
						if not c.rowcount == 0:
							"""Pilot exists already"""
							pil = 0 + c.fetchone()['ID']
							name = c.fetchone()['Name']
							message += ("FAI n. {} exists associated to pilot {}: id {} \n".format(pilFAI, name, pil))
						else:
							"""Insert new pilot"""
							query = ("INSERT INTO `tblExtPilot`(`pilFirstName`, `pilLastName`, `pilNat`, `pilSex`, `pilFAI`) VALUES ('{}','{}',{},'{}',{})".format(pilFName, pilLName, pilNat, pilSex, pilFAI))
							if not test == 1:
								"""Normal Mode"""
								#print ('NORMAL')
								c.execute(query)
								db.commit()
								message += ("PILOT {} {} ADDED \n".format(pilLName, pilFName))
							else:
								message += ("pilot {} {} doesn't exist so we need to add \n".format(pilLName, pilFName))
								message += ('Query: ' + query + ' \n')

				except ImportError:
					print ("Error while connecting to MySQL")
				finally:
					db.close()

		"""Print messages"""
		print (message)

def main():
	"""Main module"""
	test = 0
	"""check parameter is good."""
	if len(sys.argv) > 1:
		file = sys.argv[1]
		if len(sys.argv) > 2:
			print('Running in TEST MODE')
			test = 1

		"""Read CSV File"""
		read_membership(file, test)

	else:
		print('error: no filename found')

if __name__ == "__main__":
    main()
