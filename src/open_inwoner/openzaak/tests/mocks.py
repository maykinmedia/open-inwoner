from open_inwoner.openzaak.tests.shared import FORMS_ROOT


class ESuiteSubmissionData:
    def __init__(self):
        self.submission_1 = {
            "url": "https://dmidoffice2.esuite-development.net/formulieren-provider/api/v1/8e3ae29c-7bc5-4f7d-a27c-b0c83c13328e",
            "uuid": "8e3ae29c-7bc5-4f7d-a27c-b0c83c13328e",
            "naam": "Melding openbare ruimte",
            "vervolgLink": "https://dloket2.esuite-development.net/formulieren-nieuw/formulier/start/8e3ae29c-7bc5-4f7d-a27c-b0c83c13328e",
            "datumLaatsteWijziging": "2023-02-13T14:02:00.999+01:00",
            "eindDatumGeldigheid": "2023-05-14T14:02:00.999+02:00",
        }
        self.submission_2 = {
            "url": "https://dmidoffice2.esuite-development.net/formulieren-provider/api/v1/d14658b0-dcb4-4d3c-a61c-fd7d0c78f296",
            "uuid": "d14658b0-dcb4-4d3c-a61c-fd7d0c78f296",
            "naam": "Indienen bezwaarschrift",
            "vervolgLink": "https://dloket2.esuite-development.net/formulieren-nieuw/formulier/start/d14658b0-dcb4-4d3c-a61c-fd7d0c78f296",
            "datumLaatsteWijziging": "2023-02-13T14:10:26.197000+0100",
            "eindDatumGeldigheid": "2023-05-14T14:10:26.197+02:00",
        }
        # note this is a weird esuite response without pagination links
        self.response = {
            "count": 2,
            "results": [
                self.submission_1,
                self.submission_2,
            ],
        }

    def install_mocks(self, m):
        m.get(
            f"{FORMS_ROOT}openstaande-inzendingen",
            json=self.response,
        )
        return self


class ESuiteTaskData:
    def __init__(self):
        self.task1 = {
            "url": "https://maykinmedia.nl",
            "uuid": "fb72d8db-c3ee-4aa0-96c1-260b202cb208",
            "identificatie": "1234-2023",
            "naam": "Aanvullende informatie gewenst",
            "startdatum": "2023-11-14",
            "formulierLink": "https://maykinmedia.nl",
        }
        self.task2 = {
            "url": "https://maykinmedia.nl",
            "uuid": "d74f6a5c-297d-43a3-a923-1774164d852d",
            "identificatie": "4321-2023",
            "naam": "Aanvullende informatie gewenst",
            "startdatum": "2023-10-11",
            "formulierLink": "https://maykinmedia.nl",
        }

    def install_mocks(self, m):
        m.get(
            f"{FORMS_ROOT}openstaande-taken",
            json={"count": 2, "results": [self.task1, self.task2]},
        )
        return self
