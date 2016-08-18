import datetime
import dateutil.parser
import os
import glob
from base64 import urlsafe_b64decode

from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
from django.conf import settings

from ...throttler import ThrottledEmailBackend


class Command(BaseCommand):
    """
        Make a report about throttled mails and/or clean up the database.
        This command should be run once per throttle interval, preferably
        not much after the interval is over, most likely from cron.
        For example, if your interval is the default 600 seconds (10 minutes),
        then run it from cron as "*/10 * * * *" or so
    """

    help = "Report on email throttling"

    def add_arguments(self, parser):

        parser.add_argument(
            '--no-clean-log',
            action='store_true',
            dest='no_clean_log',
            default=False,
            help="Keep email log"
        )

        parser.add_argument(
            '--force-email',
            action='store_true',
            dest='force_email',
            default=False,
            help="Send summary email even if there was no throttling (but only if there were emails in general)"
        )

        parser.add_argument(
            '--no-email',
            action='store_true',
            dest='no_email',
            default=False,
            help="Don't sent summary email even if there would be something to report"
        )

        parser.add_argument(
            "--start-date",
            action="store",
            dest="start_date",
            default=False,
            help="Use this as the starting time of an interval-to-check. Format is 'YYYY-MM-DD HH:MM' (UTC)"
        )

    # command handler
    def handle(self, *args, **options):

        # define our time interval
        if options['start_date']:
            bb = dateutil.parser.parse(options['start_date'])
        else:
            bb = self._bucket_begin()
        be = self._bucket_end(bb)

        # report if there are mails and either there's something to report or report is forced
        if not options['no_email']:
            self._send_report(bb, be, options['force_email'])

        if not options['no_clean_log']:
            self._clean_log(bb)

    # assemble and send email report
    @classmethod
    def _send_report(cls, bb, be, force_email):

        n_no, n_subject, n_overall, details = cls._collect_data(bb)

        subject = "Mail throttling report for {bb} -- T:{t} N:{n} S:{s} O:{o}".format(
            bb=bb.strftime('%Y-%m-%d %H:%M'),
            t=n_no+n_subject+n_overall,
            n=n_no,
            s=n_subject,
            o=n_overall,
        )

        out = ""
        out += "Report date: {bb} - {be}\n".format(bb=bb, be=be)
        out += "Total mails: {}\n".format(n_no+n_subject+n_overall)
        out += "Not throttled: {}\n".format(n_no)
        out += "Throttled on subject: {}\n".format(n_subject)
        out += "Throttled on overall amount: {}\n".format(n_overall)
        out += "\n"
        out += "T/N/S/O Subject\n"

        # dump the collection in a nice format
        for key, value in details.items():
            out += "{t}/{n}/{s}/{o}\t'{subject}'\n".format(
                t=value[ThrottledEmailBackend.THROTTLE_NO] +
                  value[ThrottledEmailBackend.THROTTLE_SUBJECT] +
                  value[ThrottledEmailBackend.THROTTLE_OVERALL],
                n=value[ThrottledEmailBackend.THROTTLE_NO],
                s=value[ThrottledEmailBackend.THROTTLE_SUBJECT],
                o=value[ThrottledEmailBackend.THROTTLE_OVERALL],
                subject=urlsafe_b64decode(key).decode('utf-8')
                )

        # send this report if there's something to say
        if (n_no+n_subject+n_overall > 0) and (force_email or n_subject > 0 or n_overall > 0):
            mail_admins(subject, out)

    # clean up the entries for the current interval from the db
    @classmethod
    def _clean_log(cls, bb):
        pattern = os.path.join(ThrottledEmailBackend.tmpdir_name,
                               ThrottledEmailBackend.file_prefix+str(bb)+"*")
        for f in glob.glob(pattern): 
            if os.path.isfile(f):
                os.remove(f)

    # assuming that the script is run not much after the current bucket started
    # calculate start time of the *previous* bucket
    @classmethod
    def _bucket_begin(cls):
        epoch_now = int(datetime.datetime.utcnow().strftime('%s'))
        return datetime.datetime.fromtimestamp(
            epoch_now - (epoch_now % ThrottledEmailBackend.interval_size) - ThrottledEmailBackend.interval_size
        )

    # calculate end time of a bucket based on the start time
    @classmethod
    def _bucket_end(cls, bb):
        return datetime.datetime.fromtimestamp(
            int(bb.strftime('%s')) + ThrottledEmailBackend.interval_size
        )

    # get number of total, subject/overall filtered messages for a bucket
    # and all details too
    @classmethod
    def _collect_data(cls, bb):
        n_no = 0
        n_subject = 0
        n_overall = 0
        collector = {}

        pattern = os.path.join(ThrottledEmailBackend.tmpdir_name,
                               ThrottledEmailBackend.file_prefix + str(bb) + "*")
        for f in glob.glob(pattern):
            if os.path.isfile(f):
                subject = f[f.index('^')+1:]

                collector[subject] = {}
                with open(os.path.join(ThrottledEmailBackend.tmpdir_name, f),
                          "r") as subject_file:
                    content = subject_file.read()

                    # count
                    this_no = content.count(str(ThrottledEmailBackend.THROTTLE_NO))
                    this_subject = content.count(str(ThrottledEmailBackend.THROTTLE_SUBJECT))
                    this_overall = content.count(str(ThrottledEmailBackend.THROTTLE_OVERALL))

                    # store per subject and update totals
                    collector[subject][ThrottledEmailBackend.THROTTLE_NO] = this_no
                    collector[subject][ThrottledEmailBackend.THROTTLE_SUBJECT] = this_subject
                    collector[subject][ThrottledEmailBackend.THROTTLE_OVERALL] = this_overall
                    n_no += this_no
                    n_subject += this_subject
                    n_overall += this_overall

        return n_no, n_subject, n_overall, collector

