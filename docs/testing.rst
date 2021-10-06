.. _testing:

=======
Testing
=======

This document covers the tools to run tests and how to use them.


Django tests
============

Run the project tests by executing::

    $ python src/manage.py test src --keepdb

To measure coverage, use ``coverage run``::

    $ coverage run src/manage.py test src --keepdb

It may be convenient to add some aliases::

    $ alias runtests='python src/manage.py test --keepdb'
    $ runtests src

and::

    $ alias cov_runtests='coverage run src/manage.py test --keepdb'
    $ cov_runtests src && chromium htmlcov/index.html


Javascript tests
================

There are quite some options to run the Javascript tests. Karma is used as
test-runner, and you need to install it globally if you have never done so::

    $ sudo npm install -g karma

By default, the tests are run against Chrome/Chromium. To run
the tests, execute::

    $ npm test

If you want to target a single browser, you can run karma directly::

    $ karma start karma.conf.js --single-run --browsers=PhantomJS

Coverage reports can be found in ``build/reports/coverage``.

To trigger a test run on file change (source file or test file), run::

    $ karma start karma.conf.js --single-run=false --browsers=PhantomJS


