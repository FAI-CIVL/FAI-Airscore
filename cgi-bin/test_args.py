import smtplib
import sys
import logging
import argparse

from myconn import Database

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
        header = 'To:' + ','.join(email_to) + '\n' + 'From: ' + \
            self.username + '\n' + 'Subject: ' + subject + '\n'
        msg = header + '\n\n ' + body + ' \n\n'
        self.smtpserver.sendmail(self.username, email_to, msg)

    def close(self):
        '''closeconnection'''
        self.smtpserver.close()


def get_email_list(task_id, DB_User, DB_Password, DB, to_all):
    """Get pilot emails (pilots in task without tracks) 
    returns a dictionary of pilFirstName pilLastname:pilEmail."""

    db = pymysql.connect(user=DB_User, passwd=DB_Password, db=DB)
    c = db.cursor()

    where = "where A.traPk is null"
    if to_all:
        where = ''

    query = (" SELECT "
            "       P.pilFirstName, "
            "       P.pilLastName, "
            "       P.pilEmail "
            "   FROM "
            "       PilotView P "
            "       JOIN tblRegistration R ON P.pilPk = R.pilPk "
            "       LEFT OUTER JOIN ("
            "           SELECT "
            "               comPk, "
            "               tasPk, "
            "               TR.traPk, "
            "               pilPk "
            "           FROM "
            "               tblComTaskTrack TR "
            "               join tblTrack T ON TR.traPk = T.traPk "
            "           WHERE "
            "               tasPk = %s "
            "       ) AS A on R.pilPk = A.pilPK "
            "       AND R.comPk = A.comPk " + where,
              (task_id,))

    with Database() as db:
        pilot_list = dict((FirstName + ' ' + LastName, pilEmail)
                      for FirstName, LastName, pilEmail in db.fetchall(query))

    return pilot_list


def get_task_details(task_id, DB_User, DB_Password, DB):
    """Get task date and location for email subject line."""

    query = ("SELECT tasDate, comLocation FROM `tblTask` t JOIN "
              "tblCompetition c ON t.comPk = c.comPk WHERE tasPk = %s", (task_id,))
    with Database() as db:
        date, location = db.fetchone(query)

    datestr = date.strftime('%m-%d')  # convert from datetime to string
    subject = datestr + ' ' + location
    return subject


def check_arg(args=None):

    parser = argparse.ArgumentParser()

    parser.add_argument('tasPk', help='task id') #, type=int
    parser.add_argument('file', help='email text file')
    parser.add_argument('-a', '--all', help='send email to all pilots in task, '
                        'default only pilots missing tracks', action='store_true')
    parser.add_argument('-c', '--confirm', help='send confirmation to admins', action='store_true')
    parser.add_argument('-t', '--test', help='send email only to test address')

    results = parser.parse_args(args)
    return(results.tasPk, results.all, results.confirm, results.test, results.file)


def main():
    """Main module. Takes tasPk as parameter"""

    server = "mail.legapilotiparapendio.it" ##mail server
    username = 'noreply@legapilotiparapendio.it' ##mail server user
    password = 'Airscore01' #mail server password

    email_dir = '../email/'
    body = ''
    no_email = list()
    send_list = list()
    confirm_email = list()
    confirm_mess = ''
    email_to = list()

    print('Number of arguments:', len(sys.argv), 'arguments.')
    print('Argument List:', str(sys.argv))


    task_id=str(sys.argv[1])
    message_file =str(sys.argv[2])
    print(str(task_id))
    print(message_file+str(task_id))
    '''
    task_id, to_all, confirm, test, message_file = check_arg(sys.argv[
                                                                   1:])
    print(task_id)
    print(to_all)
    print(confirm)
    print(test)
    print(message_file)'''

if __name__ == "__main__":
    main()
