import arrow
import os, glob

from django.core.mail.backends.base import BaseEmailBackend
from django.core import mail
from django.conf import settings


class ThrottledEmailBackend(BaseEmailBackend):

    THROTTLE_NO = 0
    THROTTLE_SUBJECT = 1
    THROTTLE_OVERALL = 2

    tmpdir_name = getattr(settings, 'EMAILTHROTTLER_TMPDIR', '/tmp')
    file_prefix = getattr(settings, 'EMAILTHROTTLER_PREFIX', 'emailthrottler-')
    interval_size = getattr(settings, 'EMAILTHROTTLER_INTERVAL', 600)
    subject_threshold = getattr(settings, 'EMAILTHROTTLER_SUBJECT_THRESHOLD', 3)
    overall_threshold = getattr(settings, 'EMAILTHROTTLER_OVERALL_THRESHOLD', 15)

    # note: there's no open() an close()

    def send_messages(self, email_messages):

        bb = self._bucket_begin()
        in_bucket_total = self._get_in_bucket_sofar(bb)

        to_send = []
        for message in email_messages:

            throttled = ThrottledEmailBackend.THROTTLE_NO

            # it'd be possible to cache this, but it's probably not worth it
            same_subj = self._get_same_subject_sofar(bb, message.subject)

            # check for overall throttling
            if ThrottledEmailBackend.overall_threshold>0 and in_bucket_total >= ThrottledEmailBackend.overall_threshold:
                throttled = ThrottledEmailBackend.THROTTLE_OVERALL
                #print("THROTTLE_OVERALL")

            # check for subject throttling
            elif ThrottledEmailBackend.subject_threshold>0 and same_subj >= ThrottledEmailBackend.subject_threshold:
                throttled = ThrottledEmailBackend.THROTTLE_SUBJECT
                #print("THROTTLE_SUBJECT")

            # seems to be below all thresholds, send it
            else:
                message.extra_headers['X-Mail-Throttler'] = (
                    'overall={overall}, nsubj={nsubj}'.format(
                        overall=in_bucket_total+1,
                        nsubj=same_subj+1
                    )
                )
                to_send.append(message)
                throttled = ThrottledEmailBackend.THROTTLE_NO
                #print("THROTTLE_NO")

            self._save_email_info(bb, message, throttled)
            in_bucket_total += 1

        connection = mail.get_connection()
        connection.open()
        connection.send_messages(to_send)
        connection.close()


    # calculate the beginning of the current bucket
    def _bucket_begin(self):
        epoch_now = arrow.utcnow().timestamp
        return arrow.get(epoch_now - epoch_now%ThrottledEmailBackend.interval_size).datetime


    # get total number of messages in the current bucket
    def _get_in_bucket_sofar(self, bb):
        sum = 0
        pattern = os.path.join(ThrottledEmailBackend.tmpdir_name, ThrottledEmailBackend.file_prefix+str(bb)+"*") 
        for f in glob.glob(pattern): 
            if os.path.isfile(f):
                sum += os.stat(f).st_size 
        return sum


    # get number messages in the current bucket with a given subject
    def _get_same_subject_sofar(self, bb, subject):
        try:
            return os.stat(os.path.join(ThrottledEmailBackend.tmpdir_name, ThrottledEmailBackend.file_prefix+str(bb)+"^"+subject)).st_size
        except FileNotFoundError:
            return 0


    # record meta info about this mail
    def _save_email_info(self, bb, message, throttled):
        with open(os.path.join(ThrottledEmailBackend.tmpdir_name, ThrottledEmailBackend.file_prefix+str(bb)+"^"+message.subject),"a") as out:
            out.write(str(throttled))
