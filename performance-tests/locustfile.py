from urllib.parse import urlencode

from locust import HttpUser, events, task


class OpenInwonerUser(HttpUser):
    wait_time = lambda _: 0.5

    @task
    def mijn_aanvragen_list_cached(self):
        self.client.get("/mijn-aanvragen/content", headers={"HX-Request": "true"})

    def on_start(self):
        params = urlencode(
            {
                "acs": f"{self.host}/digid/acs/",
                "next": self.host,
                "cancel": f"{self.host}/accounts/login/",
            }
        )
        digid_login_url = f"/digid/idp/inloggen_ww/?{params}"

        response = self.client.get(digid_login_url)
        csrftoken = response.cookies["csrftoken"]

        self.client.post(
            digid_login_url,
            data={
                "auth_name": self.bsn,
                "auth_pass": "foo",
                "csrfmiddlewaretoken": csrftoken,
                "commit": "Inloggen",
            },
        )

        # Ensure uncached call is logged separately
        self.client.get(
            "/mijn-aanvragen/content?_uncached=true", headers={"HX-Request": "true"}
        )


@events.init_command_line_parser.add_listener
def init_parser(parser):
    parser.add_argument("--bsn", type=str, dest="bsn", help="BSN used to login with")


@events.init.add_listener
def on_locust_init(environment, **kwargs):
    OpenInwonerUser.bsn = environment.parsed_options.bsn
