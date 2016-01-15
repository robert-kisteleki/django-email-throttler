An email throttler for Django
=============================

Django error logging and emailing on a busy website can send a *lot* of emails,
all of them containing large traces. This can quickly become a bottleneck.

However, if there's an actual problem, most of the mails just repeat what's
already reported, so there's not much point in sending them all; a "sample" is
enough. It's useful to filter out repeating ones. This package does exactly
that.

It is possible to use this for something else than error-report-throttling,
but since the purpose is to hold back some emails, it may hurt you more than
it helps.


How Does it Work?
-----------------

The package contains a Django email backend that has a local cache of what
emails were sent (based on subjec, not content). If the total amount of mails
per time unit goes over an overall threshold, then the excess is just logged,
not sent out. Similarly, if the amount of mails with the same subject line is
over a threshold, then the excess is just logged, not sent out. Both
thresholds are optional and they can be different.

The mails that are not throttled are sent out with the regular Django SMTP
backend. They have an additional "X-Mail-Throttler" header which also records
bits of statistics about the current values for threshold counters.

The package includes a management command that can be run from cron. If there
are any throttled emails, then this will provide a report including statistics
about how many mails have been held back.

The cache is mainained in file on the filesystem. The method used is highly
efficient for this purpose, and doing something similar in a database could
quickly lead to performance issues which will make the overload worse, not
better.


Installation and Configuration
------------------------------

Dependency: arrow

Install the package with pip, for example. *TODO*

Settings and Defaults
~~~~~~~~~~~~~~~~~~~~~

Add these to your settings:

.. code:: bash

    # stuff for email throttling and their defaults
    EMAILTHROTTLER_TMPDIR = '/tmp'
    EMAILTHROTTLER_PREFIX = 'emailthrottler-'
    EMAILTHROTTLER_INTERVAL = 600
    EMAILTHROTTLER_SUBJECT_THRESHOLD = 3 # 0 for no-check
    EMAILTHROTTLER_OVERALL_THRESHOLD = 15 # 0 for no-check

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
        'handlers': {
            'mail_admins': {
                'level': 'ERROR',
                'class': 'django.utils.log.AdminEmailHandler',
                'email_backend': 'emailthrottler.throttler.ThrottledEmailBackend',
                'include_html': True,
            }
        },
        'loggers': {
            'django.request': {
                'handlers': ['mail_admins'],
                'level': 'ERROR'
            },
        }
    }


Admin Mailing Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

You should add a crontab entry to mail out the statistics, and clean the
database. Make sure the frequency you do this is aligned to the intervals
you set. Something like this woould work:

.. code:: bash

    */10 * * * * $WHATEVER_PATH/manage.py threshold_reporting

