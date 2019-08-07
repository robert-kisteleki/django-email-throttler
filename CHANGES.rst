Release History
===============

0.4.0 (2019-08-07)
------------------

- Python3 support (thanks @chrisamin!)


0.3.4 (2018-04-19)
------------------

- Added EMAILTHROTTLER_TRUNCATE_SUBJECT (integer) to configuration to limit
  the length of file names created by the middleware. This can come handy if
  you hit file system limitations. Default value is None.


0.3.3 (2016-09-20)
------------------

- Use "requires_system_checks = False" to disable system checks on startup.
  It comes handy e.g. when the main database in unavailable: this way the
  reporting still works.


0.3.2 (2016-08-18)
------------------

- change optparse to argparse, which is enforced by Django 1.10


0.3.1 (2016-01-26)
------------------

- pypi was acting up, bumping version to re-publish


0.3.0 (2016-01-26)
------------------

- use OSError instead of FileNotFoundError for python 2 compatibility


0.2.7 (2016-01-26)
------------------

- encode email subjects as urlsafe_base64 to avoid filename problems


0.2.6 (2016-01-24)
------------------

- clean up pypi packaging


0.2.5 (2016-01-18)
------------------

- Change to a proper app name: django_email_throttler


0.2.3 (2016-01-18)
------------------

- Various changes to make a pypi package


0.2.1 (2016-01-18)
------------------

- Adding a MANIFEST.in


0.2.0 (2016-01-18)
------------------

- Applied some wisdom from @searchingfortao
- Remove dependency on arrow at the expense of having to use ISO8601 when
  specifying the --start-date option


0.1.0 (2016-01-15)
------------------

Initial release
~~~~~~~~~~~~~~~

- support for file based bookkeeping
- support for per subject and overall limits
- support for variable bucketing
- support for reporting or not, log cleanup or not
