Permissions Policy and violation reports
========================================

Open Inwoner sends a `Permissions-Policy`_ header with every response. It
tells browsers which capabilities, called *features* (camera, microphone,
geolocation, payment, ...), pages may use. Features the application does not
need are denied, so injected or third-party scripts cannot use them either.

The policy only allows:

* ``autoplay`` and ``fullscreen``, for the page itself and the embedded YouTube
  and Vimeo players of the video plugin;
* ``publickey-credentials-get`` and ``publickey-credentials-create``, for
  WebAuthn two-factor authentication in the admin;
* ``clipboard-write``, for the page itself.

All other common features are denied.

.. note::

   The policy applies to the page, not to where a script is loaded from.
   Scripts running in our pages, such as custom JavaScript, are covered by
   the same rules as our own code. Only iframes
   from other origins need to be allowed explicitly.

.. _Permissions-Policy: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Permissions-Policy


Report-only mode
----------------

With ``PERMISSIONS_POLICY_REPORT_ONLY`` enabled, the same policy is sent as
``Permissions-Policy-Report-Only``: violations are reported, but nothing is
blocked. Use this to check what a policy would break before enforcing it, for
example when custom JavaScript or third-party widgets are in use:

1. Enable ``PERMISSIONS_POLICY_REPORT_ONLY``.
2. Use the site for a representative period, and watch the violation reports
   (see below).
3. When there are no unexpected violations, disable
   ``PERMISSIONS_POLICY_REPORT_ONLY`` to enforce the policy.

Only Chromium-based browsers (Chrome, Edge, ...) support report-only mode.
Other browsers ignore the header, so they apply no policy at all while it is
active.


Violation reports
-----------------

Browsers report violations to ``/api/reporting-api/``, which the application
declares as the default endpoint of the `Reporting API`_ through the
``Reporting-Endpoints`` header. The endpoint receives two kinds of reports:

``permissions-policy-violation``
    A page used a feature the policy does not allow.

``potential-permissions-policy-violation``
    An iframe requested a feature, through its ``allow`` attribute, that the
    policy does not allow.

Browsers send other report types to the default endpoint too, such as
deprecation warnings; these are ignored.

Each violation is:

* logged as a ``permissions_policy_violation`` warning by the
  ``reporting_api`` logger, with the feature, the page (without query string),
  the offending script and the user agent. At most a few violations are
  logged per request; the rest are summarized in a single
  ``permissions_policy_violations_not_logged`` entry.
* counted in the OpenTelemetry metric
  ``oip.reporting_api.permissions_policy_violations``, with the attributes
  ``type``, ``feature``, ``disposition`` (``enforce`` or ``report``) and
  ``source`` (``self`` for our own scripts, ``external`` for scripts from
  other hosts, ``unknown`` when the browser does not report a script).

Only reports about pages on the configured ``ALLOWED_HOSTS`` are processed.
Other reports are counted in the metric
``oip.reporting_api.rejected_reports``, with ``reason`` set to
``unknown_host``. If all reports end up there, make sure the reverse proxy
passes the original ``Host`` header and ``ALLOWED_HOSTS`` contains the public
host name.

.. note::

   Browsers only send reports over HTTPS (or plain HTTP on ``localhost``),
   and only Chromium-based browsers send them at all. In a local development
   setup without HTTPS, violations only show up in the browser console.

.. _Reporting API: https://developer.mozilla.org/en-US/docs/Web/API/Reporting_API


Monitoring
----------

The metrics are best for trends and alerts, the logs for finding the cause of
a specific violation.

**During a report-only rollout**, every violation is something that would
break once the policy is enforced. Look at the violations metric with
``disposition="report"``, grouped by ``feature`` and ``source``:

* ``source="self"`` points to our own code, which is a bug to fix.
* ``source="external"`` points to a third-party script, such as custom
  JavaScript, analytics or a widget.
* ``type="potential-permissions-policy-violation"`` points to an embedded
  iframe asking for a feature.

For each feature that shows up, the ``permissions_policy_violation`` log
entries of the ``reporting_api`` logger tell which page (``url``) and which
script (``source_file``, ``line_number``) caused it.

**Once the policy is enforced**, violations mean something is blocked for real
users. Alert on an increase of violations with ``disposition="enforce"``,
for example after a release (``source="self"``) or a change to custom
JavaScript or third-party scripts (``source="external"``).

**In both cases**, alert when ``oip.reporting_api.rejected_reports`` keeps
increasing while no violations are counted: that points to a misconfigured
``ALLOWED_HOSTS`` or reverse proxy rather than an absence of violations.

The metric names in the monitoring backend depend on the exporter. With the
Prometheus exporter, dots become underscores and counters get a ``_total``
suffix, possibly with a prefix (``otel_`` in the Docker Compose setup). For
example, the violations per feature that would break when enforced:

.. code-block:: promql

    sum by (feature, source) (
      increase(otel_oip_reporting_api_permissions_policy_violations_total{disposition="report"}[1d])
    )

In the logs, filter on ``logger="reporting_api"`` and
``event="permissions_policy_violation"``. A
``permissions_policy_violations_not_logged`` entry means a browser sent more
violations at once than are logged per request; they are still counted in the
metric.

.. note::

   Anyone can send reports to the endpoint, so treat the numbers as a signal
   to investigate, not as proof. A sudden spike from a single ``url`` or
   ``user_agent`` is more likely noise than a real problem.


Configuration
-------------

The following environment variables control the policy and the reports, see
:doc:`02_env_vars` for details:

``PERMISSIONS_POLICY_REPORT_ONLY``
    Report violations instead of blocking them.

``REPORTING_API_ENABLED``
    Ask browsers to send reports at all. When disabled, the policy is still
    applied, but browsers send no reports and the endpoint is unavailable.

``REPORTING_API_LOGGING_ENABLED`` and ``REPORTING_API_METRICS_ENABLED``
    Log violations and/or count them in the metric. When both are disabled
    while reporting is enabled, the system check ``reporting_api.W001`` warns
    that received reports are discarded.

``REPORTING_API_MAX_REPORTS_PER_REQUEST`` and ``REPORTING_API_MAX_LOGGED_VIOLATIONS_PER_REQUEST``
    Bound the work and the log volume a single request can cause.


Rate limiting
-------------

The endpoint has to accept reports from anonymous visitors, so anyone can send
requests to it. The application validates every report and limits what a
single request can cause, but it does not limit the number of requests.
We recommend rate limiting the endpoint in the reverse proxy, before requests
reach the application.

Browsers send reports in batches, about once a minute per page, so legitimate
traffic per visitor is low. An example for nginx:

.. code-block:: nginx

    # outside the server block, i.e. in the http context
    limit_req_zone $binary_remote_addr zone=reporting_api:1m rate=10r/m;

    server {
        # ...

        location = /api/reporting-api/ {
            limit_req zone=reporting_api burst=10 nodelay;
            limit_req_status 429;
            # browsers send small batches of a few kilobytes
            client_max_body_size 64k;

            proxy_pass http://web:8000;
            proxy_set_header Host $http_host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }

This allows each client 10 requests per minute, with bursts of up to 10
more, and rejects anything else with a ``429`` before it reaches the
application. Rejected reports are lost, but browsers retry them a few times.

.. note::

   ``$binary_remote_addr`` is the address of the client connecting to nginx.
   If nginx runs behind another proxy or load balancer, configure the
   `real IP module`_ so it is the visitor's address. Otherwise all visitors
   share a single limit.

.. _real IP module: https://nginx.org/en/docs/http/ngx_http_realip_module.html
