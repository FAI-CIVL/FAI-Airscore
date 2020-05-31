#!/home/untps52y/opt/python-3.6.2/bin/python3
"""email pilots script. Can send email to pilots with no track
submitted
(default e.g. for sending a reminder to submit)
or to all pilots in task
(e.g.for sending results available)
arguments <tas_id>  <text file> optional(-a to all pilots, -t <TEST> send only to test email)
email text file located in email_dir.
task date and comp location
followed by first line of email text file is the subject.
Rest of email text file is message body.
Will send a confirmation to all comp admins unless in -t test mode.
"""

import argparse
import smtplib

from db.conn import db_session
from sqlalchemy.exc import SQLAlchemyError


class send_mail():
    def __init__(self, server, username, password):
        """make connection"""

        self.server = server
        self.username = username
        self.password = password
        self.smtpserver = smtplib.SMTP(server, 25)
        self.smtpserver.ehlo()
        self.smtpserver.login(username, password)

    def send(self, email_to, subject, body):
        """send email"""
        email_to_for_header = email_to
        if isinstance(email_to, list):  # if we have a list of addresses, make a string with separating commas.
            email_to_for_header = ', '.join(email_to)
        header = 'To:' + email_to_for_header + '\n' + 'From: ' + \
                 self.username + '\n' + 'Subject: ' + subject + '\n'
        msg = header + '\n\n ' + body + ' \n\n'
        self.smtpserver.sendmail(self.username, email_to, msg.encode("ascii", errors="replace"))

    def close(self):
        """close connection"""
        self.smtpserver.close()


def get_email_list(task_id, to_all=None):
    """Get pilot emails (pilots in task without tracks)
    returns a dictionary of pilFirstName pilLastname:pilEmail."""
    from db.tables import TblParticipant as R, PilotView as P, TblTaskResult as S, TblTask as T
    from sqlalchemy import and_

    with db_session() as db:
        comp_id = db.query(T).get(task_id).comp_id
        q = (db.query(R.name, P.email).join(P, P.pil_id == R.pil_id).outerjoin(
            S, and_(R.pil_id == S.pil_id, S.task_id == task_id))).filter(R.comp_id == comp_id)
        if not to_all:
            q = q.filter(S.track_id.is_(None))
        result = q.all()

        pilot_list = dict((x.name, x.email) for x in result)
    return pilot_list


def get_task_details(task_id):
    """Get task date and location for email subject line."""
    from db.tables import TblCompetition as C, TblTask as T

    with db_session() as db:
        q = db.query(T.date, C.comp_site).join(C, C.comp_id == T.comp_id).filter(T.task_id == task_id)
        date, location = q.one()
    datestr = date.strftime('%m-%d')  # convert from datetime to string
    subject = datestr + ' ' + location
    return subject


def get_admin_email(task_id, DB_User, DB_Password, DB):
    """Get admin email addresses"""
    from db.tables import UserView as U, TblCompAuth as C, TblTask as T

    with db_session() as db:
        q = db.query(U.user_email).join(C, C.user_id == U.user_id).join(T, T.comp_id == C.comp_id)
        users = q.filter(T.task_id == task_id).all()
        return [u[0] for u in users]


def get_args(args=None):
    print('Number of arguments:', len(args), 'arguments.<br />')
    print('Argument List:', str(args), '<br />')
    try:
        task_id = str(args[0])
        message_file = str(args[1])
        print('task ID: ', task_id, '<br />')
        print('Message File: ', message_file, ' <br />')
        print('Argument List again:', str(args))
    except ImportError:
        raise SystemExit('Something went terribly wrong.')


def check_arg(args=None):
    parser = argparse.ArgumentParser()

    parser.add_argument('task_id', help='task id', type=int)
    parser.add_argument('file', help='email text file')
    parser.add_argument('-a', '--all', help='send email to all pilots in task, '
                                            'default only pilots missing tracks', action='store_true')
    parser.add_argument('-t', '--test', help='send email only to test address')

    results = parser.parse_args(args)
    return (results.task_id, results.all, results.test, results.file)


def main():
    """"""


#     server = "mail.legapilotiparapendio.it" ##mail server
#     username = 'noreply@legapilotiparapendio.it' ##mail server user
#     password = '' #mail server password
#     app_dir = '/app/airscore'
#
#     email_dir = app_dir + 'email/'
#     body = ''
#     no_email = list()
#     send_list = list()
#     confirm_email = list()
#     confirm_mess = ''
#     email_to = list()
#
#     task_id, to_all, test_email, message_file = check_arg(sys.argv[1:])
# #   print('task ID from parser: ', task_id, '<br />')
# #   print('Message File: ', message_file,' <br />')
# #   print('Message to All: ', to_all,' <br />')
# #   print("<br />")
#     pilot_list = get_email_list(task_id, MYSQLUSER, MYSQLPASSWORD, DATABASE, to_all)
# #   print('I got pilots list from get_email_list <br />')
#     subject = get_task_details(task_id, MYSQLUSER, MYSQLPASSWORD, DATABASE)
# #   print('I got task details from get_task_details <br />')
#
#     # setup smtp connection
#     mail = send_mail(server, username, password)
# #   print('Got setup from send_mail <br />')
#
#     # have we got anyone in the list
#     if len(pilot_list) > 0:
# #       print('We have pilots in list <br />')
#         for name in pilot_list:
#             if not pilot_list[name]:
#                 no_email.append(' ' + name)
#             else:
#                 email_to.append(pilot_list[name])
#                 send_list.append(name + ' ' + pilot_list[name])
#
#         # check if we are in test mode (if so, we don't send email to pilots)
#         if test_email:
#             print('<strong style=\'color:red\'>We are in Test Mode, email will NOT be sent to pilots, only ', test_email, ' will receive it</strong><br />')
#             email_to = test_email
#
#         with open(email_dir + message_file, 'r') as mess:
#             subject += ' '+ mess.readline()
#             body = ''.join(mess.readlines())
#             print('<hr />Email Subject: ', subject, ' <br />')
#             print('Email Body: <pre>', body, ' </pre><br /><hr />')
#
#         if not test_email:
#           mail.send(email_to, subject, body)
#           print('We correctly sent mail to recipients.  <br />')
#
#     else:
#         logging.info('No pilots to get')
#         confirm_mess = 'No pilots to get\n'
#
#     print('<strong>Confirmation message to Admins SENT</strong><br />')
#     if len(no_email) > 0:
# #       print('There are some pilots with no email address <br />')
#         confirm_mess += 'the following pilots have no email address in the DB:\n{}'.format('\n '.join(no_email)) + '\n'
#     confirm_mess += 'the following pilots were sent an email:\n{}'.format('\n '.join(send_list)) + '\n'
#     confirm_mess += '\nBody Email:\n' + body
#     confirm_email = get_admin_email(task_id, MYSQLUSER, MYSQLPASSWORD, DATABASE)
#     print(confirm_email)
#     if not test_email:
#         print('Admins email: ', list(enumerate(confirm_email)), ' <br />')
#         #print(confirm_mess, ' <br />')
#         print(isinstance(email_to, list))
#         mail.send(confirm_email, subject + ' Airscore email confirmation', confirm_mess)
#         print("sent")
#
#     else: ####test mode####
#         confirm_mess = '***TEST EMAIL***\n' + confirm_mess
#         confirm_mess = confirm_mess.replace('were sent','would have been sent')
#         #print(confirm_mess+' <br />')
#         mail.send(test_email, subject} + ' TEST EMAIL', confirm_mess)
#
#     mail.close()

if __name__ == "__main__":
    main()
