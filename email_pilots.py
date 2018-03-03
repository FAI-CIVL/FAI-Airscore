#!/usr/bin/python
'''email pilots script. Can send email to pilots with no track 
submitted (default e.g. for sending a reminder to submit) 
or to all pilots in task (e.g.for sending results available)

arguments <tasPk>  <text file> optional(-a to all pilots, -c <CONFIRMATION> send 
email with confirmation, -t <TEST> send only to test email)  

email text file located in email_dir. task date and comp location 
followed by first line of email text file is the subject. 
Rest of email text file is message body.
  '''
import smtplib
import sys
import MySQLdb
import logging
import argparse

class send_mail():

    def __init__(self, server, username, password):
        '''make connection'''
        self.server = server
        self.username = username
        self.password = password
        self.smtpserver = smtplib.SMTP(server, 25)
        self.smtpserver.ehlo()
        self.smtpserver.login(username, password)

    def send(self, email_to, subject, body):
        '''send email'''
        header = 'To:' + email_to + '\n' + 'From: ' + \
            self.username + '\n' + 'Subject: ' + subject + '\n'
        msg = header + '\n\n ' + body + ' \n\n'
        self.smtpserver.sendmail(self.username, email_to, msg)

    def close(self):
        '''closeconnection'''
        self.smtpserver.close()


def get_email_list(task_id, DB_User, DB_Password, DB, to_all):
    """Get pilot emails (pilots in task without tracks) 
    returns a dictionary of pilFirstName pilLastname:pilEmail."""

    db = MySQLdb.connect(user=DB_User, passwd=DB_Password, db=DB)
    c = db.cursor()

    where = "where a.traPk is null"
    if to_all:
        where = ''

    c.execute("SELECT pilFirstName, p.pilLastname, pilEmail FROM tblPilot p "
              "join tblCompPilot b on p.pilPk = b.pilPk left outer join "
              "(SELECT comPk, tasPk, c.traPk, pilPk FROM tblComTaskTrack c "
              "join tblTrack t on c.traPk = t.traPk where tasPk= %s) as a "
              "on b.pilPk = a.pilPK and b.comPk = a.comPk " + where,
              (task_id,))

    pilot_list = dict((FirstName + ' ' + LastName, pilEmail)
                      for FirstName, LastName, pilEmail in c.fetchall())
    return pilot_list


def get_task_details(task_id, DB_User, DB_Password, DB):
    """Get task date and location for email subject line."""

    db = MySQLdb.connect(user=DB_User, passwd=DB_Password, db=DB)
    c = db.cursor()

    c.execute("SELECT tasDate, comLocation FROM `tblTask` t join "
              "tblCompetition c on t.comPk = c.comPk WHERE tasPk = %s", (task_id,))
    date, location = c.fetchone()
    datestr = date.strftime('%m-%d')  # convert from datetime to string
    subject = datestr + ' ' + location
    return subject

def check_arg(args=None):

    parser = argparse.ArgumentParser()

    parser.add_argument('tasPk', help='task id', type=int)
    parser.add_argument('file', help='email text file')
    parser.add_argument('-a', '--all', help='send email to all pilots in task, '
                        'default only pilots missing tracks', action='store_true')
    parser.add_argument('-c', '--confirm', help='send confirmation to email')
    parser.add_argument('-t', '--test', help='send email only to test address')

    results = parser.parse_args(args)
    return(results.tasPk, results.all, results.confirm, results.test, results.file)


def main():
    """Main module. Takes tasPk as parameter"""
    DB_User = 'xxxxxxxxxxxxx'  # mysql db user
    DB_Password = 'xxxxxxxxxxx'  # mysql db password
    DB = 'xcdb'  # mysql db name

    server = 'xxxxxxxxxxxxxx' ##mail server
    username = 'xxxxxxxxxxxx' ##mail server user
    password = 'xxxxxxxxxxx' #mail server password
    
    email_dir = '/var/www/email/'
    body = ''
    no_email = list()
    send_list = list()
    confirm_email = ''
    confirm_mess = ''
    email_to = ''

    task_id, to_all, confirm_email, test, message_file = check_arg(sys.argv[
                                                               1:])
    pilot_list = get_email_list(task_id, DB_User, DB_Password, DB, to_all)
    subject = get_task_details(task_id, DB_User, DB_Password, DB)
    # setup smtp connection
    mail = send_mail(server, username, password)

    # have we got anyone in the list
    if len(pilot_list) > 0:
        for name in pilot_list:
            if pilot_list[name] == None:
                no_email.append(' ' + name)
            else:
                email_to += pilot_list[name] + ', '
                send_list.append(name + ' ' + pilot_list[name])

        # check if we are in test mode (if so, we don't send email to pilots)
        if test:
            email_to = test

        with open(email_dir + message_file, 'r') as mess:
            subject += ' '+ mess.readline()
            body = "".join(mess.readlines())

        mail.send(email_to, subject, body)

    else:
        logging.info("No pilots to get")
        confirm_mess = "No pilots to get\n"

    if confirm_email:
        if len(no_email) > 0:
            confirm_mess += "the following pilots have no email address in the DB:\n{}".format(
                '\n'.join(no_email)) + '\n'
        confirm_mess += "the following pilots were sent an email:\n{}".format(
            '\n'.join(send_list))
        confirm_mess += '\n\n\nemail:\n' + body
        print(confirm_mess)
        mail.send(confirm_email, subject +
                  ' Airscore email confirmation', confirm_mess)

    mail.close()


if __name__ == "__main__":
    main()
