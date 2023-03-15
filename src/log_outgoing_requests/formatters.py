import logging
import textwrap


class HttpFormatter(logging.Formatter):
    def formatMessage(self, record):
        result = super().formatMessage(record)
        if record.name == "requests":
            result += textwrap.dedent(
                """
                ---------------- request ----------------
                {req.method} {req.url}

                ---------------- response ----------------
                {res.status_code} {res.reason} {res.url}
                
            """
            ).format(
                req=record.req,
                res=record.res,
            )

        return result
