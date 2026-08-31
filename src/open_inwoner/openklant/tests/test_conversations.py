from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from openklant_client.exceptions import NotFound as OK2NotFound

from open_inwoner.openklant.conversations import (
    CONVERSATION_EXPAND,
    ConversationGraph,
    OpenKlantConversationFetcher,
    parent_uuid_from_expand,
)


def make_not_found() -> OK2NotFound:
    """The exception the client raises for a klantcontact that is not there."""
    return OK2NotFound(
        Mock(),
        {
            "type": "",
            "code": "not_found",
            "title": "Niet gevonden.",
            "status": 404,
            "detail": "",
            "instance": "",
        },
    )


def make_klantcontact(
    uuid,
    inhoud,
    plaatsgevonden_op,
    parent_uuid=None,
    onderwerp_objecten=None,
    interne_taak_statuses=(),
):
    """Build an expanded klantcontact, optionally replying to `parent_uuid`."""
    if onderwerp_objecten is None:
        onderwerp_objecten = [
            {
                "uuid": f"oo-{uuid}",
                "klantcontact": {"uuid": uuid},
                "wasKlantcontact": (
                    {"uuid": parent_uuid} if parent_uuid is not None else None
                ),
            }
        ]
    return {
        "uuid": uuid,
        "inhoud": inhoud,
        "onderwerp": "Philosophy",
        "kanaal": "telefoon",
        "taal": "nld",
        "nummer": uuid,
        "plaatsgevondenOp": plaatsgevonden_op,
        "url": f"http://example.com/{uuid}",
        "gingOverOnderwerpobjecten": [
            {"uuid": oo["uuid"]} for oo in onderwerp_objecten
        ],
        "_expand": {
            "gingOverOnderwerpobjecten": onderwerp_objecten,
            "leiddeTotInterneTaken": [
                {"uuid": f"taak-{uuid}-{index}", "status": status}
                for index, status in enumerate(interne_taak_statuses)
            ],
        },
    }


class FakeFetcher:
    """A `ConversationFetcher` answering from dicts instead of from the API.

    `replies` maps a klantcontact uuid to the uuids replying to it, `retrievable` maps
    a uuid to the klantcontact to return for it. A uuid in neither gets no replies and
    names nothing that can be retrieved, which is the ordinary case: the listing
    already returned the whole conversation.
    """

    def __init__(
        self,
        *,
        replies=None,
        retrievable=None,
        retrieve_complete=True,
        replies_complete=True,
    ):
        self.replies = replies or {}
        self.retrievable = retrievable or {}
        self.retrieve_complete = retrieve_complete
        self.replies_complete = replies_complete
        self.retrieve_calls = []
        self.replies_to_calls = []

    def retrieve(self, uuids):
        self.retrieve_calls.append(set(uuids))
        return [
            self.retrievable[uuid] for uuid in uuids if uuid in self.retrievable
        ], self.retrieve_complete

    def replies_to(self, uuids):
        self.replies_to_calls.append(set(uuids))
        return {
            reply_uuid for uuid in uuids for reply_uuid in self.replies.get(uuid, [])
        }, self.replies_complete


class FakeClock:
    """A stand-in for `time.monotonic` that only moves when told to."""

    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class ConversationGraphTestCase(SimpleTestCase):
    def test_a_klantcontact_that_replies_to_nothing_is_a_root(self):
        graph = ConversationGraph()
        graph.add(make_klantcontact("q1", "Question?", "2024-10-01T10:00:00Z"), None)
        graph.add(make_klantcontact("r1", "Reaction", "2024-10-02T10:00:00Z"), "q1")

        self.assertEqual(graph.root_uuids, ["q1"])
        self.assertEqual(graph.descendants("q1"), ["r1"])

    def test_descendants_collects_a_whole_chain(self):
        graph = ConversationGraph()
        graph.add(make_klantcontact("q1", "Question?", "2024-10-01T10:00:00Z"), None)
        for depth in range(1, 4):
            graph.add(
                make_klantcontact(f"r{depth}", "Reaction", "2024-10-02T10:00:00Z"),
                "q1" if depth == 1 else f"r{depth - 1}",
            )

        self.assertEqual(graph.root_uuids, ["q1"])
        self.assertEqual(graph.descendants("q1"), ["r1", "r2", "r3"])

    def test_descendants_terminates_on_a_cycle(self):
        # a -> b -> a: every klantcontact replies to another, so there is no root
        # and nothing to show, but the walk must still terminate.
        graph = ConversationGraph()
        graph.add(make_klantcontact("a", "A", "2024-10-01T10:00:00Z"), "b")
        graph.add(make_klantcontact("b", "B", "2024-10-02T10:00:00Z"), "a")

        self.assertEqual(graph.root_uuids, [])
        self.assertEqual(graph.descendants("a"), ["b"])

    def test_a_klantcontact_already_in_the_graph_is_not_added_twice(self):
        """The repair and walk passes can arrive at one the listing already returned."""
        graph = ConversationGraph()
        graph.add(make_klantcontact("q1", "Question?", "2024-10-01T10:00:00Z"), None)
        reaction = make_klantcontact("r1", "Reaction", "2024-10-02T10:00:00Z")
        graph.add(reaction, "q1")
        graph.add(reaction, "q1")

        self.assertEqual(graph.descendants("q1"), ["r1"])

    def test_a_parent_outside_the_graph_is_missing_and_leaves_an_orphan(self):
        graph = ConversationGraph()
        graph.add(make_klantcontact("r1", "Reaction", "2024-10-02T10:00:00Z"), "gone")

        self.assertEqual(graph.missing_parent_uuids, {"gone"})
        self.assertEqual(graph.orphan_uuids, ["r1"])
        # An orphan is not a root: showing it as one would present an employee's
        # reply as something the citizen asked.
        self.assertEqual(graph.root_uuids, [])


class ParentUuidTestCase(SimpleTestCase):
    def test_a_klantcontact_without_a_wasklantcontact_replies_to_nothing(self):
        klantcontact = make_klantcontact("q1", "Question?", "2024-10-01T10:00:00Z")

        self.assertIsNone(parent_uuid_from_expand(klantcontact))

    def test_a_reaction_that_also_references_a_zaak_is_not_a_question(self):
        reaction = make_klantcontact(
            "r1",
            "Reaction",
            "2024-10-02T10:00:00Z",
            onderwerp_objecten=[
                # The zaak link comes first, so stopping at the first onderwerpobject
                # without a `wasKlantcontact` would read this reaction as a question.
                {"uuid": "oo-zaak", "klantcontact": {"uuid": "r1"}},
                {
                    "uuid": "oo-r1",
                    "klantcontact": {"uuid": "r1"},
                    "wasKlantcontact": {"uuid": "q1"},
                },
            ],
        )

        self.assertEqual(parent_uuid_from_expand(reaction), "q1")

    def test_replying_to_more_than_one_klantcontact_takes_the_first(self):
        reaction = make_klantcontact(
            "r1",
            "Reaction",
            "2024-10-02T10:00:00Z",
            onderwerp_objecten=[
                {"uuid": "oo-a", "wasKlantcontact": {"uuid": "q1"}},
                {"uuid": "oo-b", "wasKlantcontact": {"uuid": "q2"}},
            ],
        )

        self.assertEqual(parent_uuid_from_expand(reaction), "q1")

    def test_a_klantcontact_without_an_expand_replies_to_nothing(self):
        self.assertIsNone(parent_uuid_from_expand({"uuid": "q1"}))


class ConversationBuildTestCase(SimpleTestCase):
    def test_a_chain_resolves_to_one_question_with_every_reaction(self):
        """An external service can link each reaction to the previous one."""
        graph, complete = ConversationGraph.build(
            [
                make_klantcontact("q1", "Question?", "2024-10-01T10:00:00Z"),
                make_klantcontact("r1", "First", "2024-10-02T10:00:00Z", "q1"),
                make_klantcontact("r2", "Second", "2024-10-03T10:00:00Z", "r1"),
                make_klantcontact("r3", "Third", "2024-10-04T10:00:00Z", "r2"),
            ],
            FakeFetcher(),
        )

        self.assertTrue(complete)
        self.assertEqual(graph.root_uuids, ["q1"])
        self.assertEqual(graph.descendants("q1"), ["r1", "r2", "r3"])

    def test_a_cycle_terminates_and_yields_no_question(self):
        graph, complete = ConversationGraph.build(
            [
                make_klantcontact("a", "A", "2024-10-01T10:00:00Z", "b"),
                make_klantcontact("b", "B", "2024-10-02T10:00:00Z", "a"),
            ],
            FakeFetcher(),
        )

        self.assertTrue(complete)
        self.assertEqual(graph.root_uuids, [])

    def test_the_walk_asks_about_every_klantcontact_exactly_once(self):
        """The ordinary case: nothing is hidden, so one round and no retrievals."""
        fetcher = FakeFetcher()

        _, complete = ConversationGraph.build(
            [
                make_klantcontact("q1", "Question?", "2024-10-01T10:00:00Z"),
                make_klantcontact("r1", "Reaction", "2024-10-02T10:00:00Z", "q1"),
            ],
            fetcher,
        )

        self.assertTrue(complete)
        self.assertEqual(fetcher.replies_to_calls, [{"q1", "r1"}])
        self.assertEqual(fetcher.retrieve_calls, [])

    def test_the_walk_finds_a_reaction_the_listing_could_not_return(self):
        """The newest reaction can carry no partij-betrokkene, so only asking finds it."""
        hidden = make_klantcontact("r1", "Hidden", "2024-10-02T10:00:00Z", "q1")
        fetcher = FakeFetcher(replies={"q1": ["r1"]}, retrievable={"r1": hidden})

        graph, complete = ConversationGraph.build(
            [make_klantcontact("q1", "Question?", "2024-10-01T10:00:00Z")], fetcher
        )

        self.assertTrue(complete)
        self.assertEqual(graph.descendants("q1"), ["r1"])

    def test_the_walk_follows_a_run_of_consecutive_hidden_reactions(self):
        """A hidden reaction can be replied to by another hidden one, without limit."""
        hidden = {
            f"r{depth}": make_klantcontact(
                f"r{depth}",
                f"Reaction {depth}",
                f"2024-10-{depth + 1:02d}T10:00:00Z",
                "q1" if depth == 1 else f"r{depth - 1}",
            )
            for depth in range(1, 13)
        }
        fetcher = FakeFetcher(
            replies={"q1": ["r1"], **{f"r{d}": [f"r{d + 1}"] for d in range(1, 12)}},
            retrievable=hidden,
        )

        graph, complete = ConversationGraph.build(
            [make_klantcontact("q1", "Question?", "2024-10-01T10:00:00Z")], fetcher
        )

        self.assertTrue(complete)
        self.assertEqual(len(graph.descendants("q1")), 12)
        # Each klantcontact is asked about once, so the walk stays linear in the
        # size of the conversation.
        self.assertEqual(len(fetcher.replies_to_calls), 13)

    def test_a_klantcontact_the_listing_returned_is_not_asked_about_again(self):
        """The walk can rediscover what is already there; it must not loop on it."""
        question = make_klantcontact("q1", "Question?", "2024-10-01T10:00:00Z")
        reaction = make_klantcontact("r1", "Reaction", "2024-10-02T10:00:00Z", "q1")
        fetcher = FakeFetcher(
            replies={"q1": ["r1"]}, retrievable={"q1": question, "r1": reaction}
        )

        graph, complete = ConversationGraph.build([question, reaction], fetcher)

        self.assertTrue(complete)
        self.assertEqual(fetcher.replies_to_calls, [{"q1", "r1"}])
        self.assertEqual(graph.descendants("q1"), ["r1"])

    def test_repair_retrieves_a_parent_the_listing_skipped(self):
        """A visible reaction can reply to one that is missing from the listing."""
        missing = make_klantcontact("r1", "Middle", "2024-10-02T10:00:00Z", "q1")
        fetcher = FakeFetcher(retrievable={"r1": missing})

        graph, complete = ConversationGraph.build(
            [
                make_klantcontact("q1", "Question?", "2024-10-01T10:00:00Z"),
                make_klantcontact("r2", "Last", "2024-10-03T10:00:00Z", "r1"),
            ],
            fetcher,
        )

        self.assertTrue(complete)
        self.assertEqual(fetcher.retrieve_calls, [{"r1"}])
        self.assertEqual(graph.descendants("q1"), ["r1", "r2"])

    def test_repair_follows_a_run_of_missing_parents(self):
        """A repaired klantcontact can itself reply to one we do not have."""
        fetcher = FakeFetcher(
            retrievable={
                "r1": make_klantcontact("r1", "First", "2024-10-02T10:00:00Z", "q1"),
                "q1": make_klantcontact("q1", "Question?", "2024-10-01T10:00:00Z"),
            }
        )

        graph, complete = ConversationGraph.build(
            [make_klantcontact("r2", "Second", "2024-10-03T10:00:00Z", "r1")], fetcher
        )

        self.assertTrue(complete)
        self.assertEqual(fetcher.retrieve_calls, [{"r1"}, {"q1"}])
        self.assertEqual(graph.root_uuids, ["q1"])

    def test_a_parent_that_cannot_be_retrieved_is_tried_once_and_is_not_incomplete(
        self,
    ):
        """Retrying would not conjure it up, so this is as complete as it gets."""
        fetcher = FakeFetcher()

        graph, complete = ConversationGraph.build(
            [
                make_klantcontact("q1", "Question?", "2024-10-01T10:00:00Z"),
                make_klantcontact("r1", "Reaction", "2024-10-02T10:00:00Z", "gone"),
            ],
            fetcher,
        )

        self.assertTrue(complete)
        self.assertEqual(fetcher.retrieve_calls, [{"gone"}])
        self.assertEqual(graph.root_uuids, ["q1"])

    def test_a_failed_walk_reports_incomplete(self):
        graph, complete = ConversationGraph.build(
            [make_klantcontact("q1", "Question?", "2024-10-01T10:00:00Z")],
            FakeFetcher(replies_complete=False),
        )

        self.assertFalse(complete)
        # What was resolved is still there, so the citizen sees the conversation in
        # part rather than an error page.
        self.assertEqual(graph.root_uuids, ["q1"])

    def test_a_failed_repair_reports_incomplete(self):
        _, complete = ConversationGraph.build(
            [make_klantcontact("r1", "Reaction", "2024-10-02T10:00:00Z", "q1")],
            FakeFetcher(retrieve_complete=False),
        )

        self.assertFalse(complete)

    def test_a_reaction_discovered_by_the_walk_is_merged_with_its_parent_link(self):
        """A discovered klantcontact is read for its own parent, not assumed to be one."""
        # `r2` replies to `r1`, not to the klantcontact the walk asked about.
        hidden_1 = make_klantcontact("r1", "First", "2024-10-02T10:00:00Z", "q1")
        hidden_2 = make_klantcontact("r2", "Second", "2024-10-03T10:00:00Z", "r1")
        fetcher = FakeFetcher(
            replies={"q1": ["r1", "r2"]},
            retrievable={"r1": hidden_1, "r2": hidden_2},
        )

        graph, complete = ConversationGraph.build(
            [make_klantcontact("q1", "Question?", "2024-10-01T10:00:00Z")], fetcher
        )

        self.assertTrue(complete)
        self.assertEqual(graph.children_of["q1"], ["r1"])
        self.assertEqual(graph.children_of["r1"], ["r2"])

    def test_the_parent_reader_can_be_replaced(self):
        """The service passes one that can retrieve onderwerpobjecten left unexpanded."""
        graph, _ = ConversationGraph.build(
            [make_klantcontact("r1", "Reaction", "2024-10-02T10:00:00Z")],
            FakeFetcher(),
            parent_uuid_for=lambda klantcontact: "q1",
        )

        self.assertEqual(graph.parent_of, {"r1": "q1"})


class OpenKlantConversationFetcherTestCase(SimpleTestCase):
    def _fetcher(self, client, *, timeout=15, clock=None):
        """Build a fetcher on a single worker, which keeps the requests inline."""
        return OpenKlantConversationFetcher(
            lambda: client, timeout=timeout, max_workers=1
        )

    def test_klantcontacten_are_retrieved_with_the_conversation_expand(self):
        """Anything missing from the expand would cost a request to fetch back."""
        klantcontact = make_klantcontact("r1", "Reaction", "2024-10-02T10:00:00Z")
        client = Mock()
        client.klant_contact.retrieve.return_value = klantcontact

        klantcontacten, complete = self._fetcher(client).retrieve(["r1"])

        self.assertTrue(complete)
        self.assertEqual(klantcontacten, [klantcontact])
        client.klant_contact.retrieve.assert_called_once_with(
            "r1", params={"expand": CONVERSATION_EXPAND}
        )

    def test_a_klantcontact_that_does_not_exist_is_dropped_but_not_incomplete(self):
        """Nothing points at a klantcontact that is there to fetch, so retrying cannot
        help and the conversation is as complete as it gets."""
        client = Mock()
        client.klant_contact.retrieve.side_effect = make_not_found()

        klantcontacten, complete = self._fetcher(client).retrieve(["gone"])

        self.assertEqual(klantcontacten, [])
        self.assertTrue(complete)

    def test_a_failing_retrieval_reports_incomplete(self):
        client = Mock()
        client.klant_contact.retrieve.side_effect = OSError("connection reset")

        klantcontacten, complete = self._fetcher(client).retrieve(["r1"])

        self.assertEqual(klantcontacten, [])
        self.assertFalse(complete)

    def test_a_failing_reply_lookup_reports_incomplete(self):
        client = Mock()
        client.onderwerp_object.list_iter.side_effect = OSError("connection reset")

        reply_uuids, complete = self._fetcher(client).replies_to(["q1"])

        self.assertEqual(reply_uuids, set())
        self.assertFalse(complete)

    def test_replies_are_read_off_the_onderwerpobjecten_pointing_at_the_klantcontact(
        self,
    ):
        client = Mock()
        client.onderwerp_object.list_iter.return_value = iter(
            [
                {"uuid": "oo-r1", "klantcontact": {"uuid": "r1"}},
                # An onderwerpobject can tie a zaak to a klantcontact instead.
                {"uuid": "oo-zaak", "klantcontact": None},
            ]
        )

        reply_uuids, complete = self._fetcher(client).replies_to(["q1"])

        self.assertTrue(complete)
        self.assertEqual(reply_uuids, {"r1"})
        self.assertEqual(
            client.onderwerp_object.list_iter.call_args.kwargs["params"][
                "wasKlantcontact__uuid"
            ],
            "q1",
        )

    def test_failure_partway_through_replies_reports_incomplete(self):
        """The pages after the first are fetched as the iterator is consumed, so a
        failure can arrive after the call returns. Consuming it where the caller
        guards it is what catches that."""

        def _replies(*, params):
            yield {"klantcontact": {"uuid": "r1"}}
            raise OSError("connection reset")

        client = Mock()
        client.onderwerp_object.list_iter.side_effect = _replies

        reply_uuids, complete = self._fetcher(client).replies_to(["q1"])

        self.assertFalse(complete)
        self.assertEqual(reply_uuids, set())

    def test_nothing_to_fetch_is_a_complete_result(self):
        client = Mock()

        self.assertEqual(self._fetcher(client).retrieve([]), ([], True))
        self.assertEqual(self._fetcher(client).replies_to([]), (set(), True))
        client.klant_contact.retrieve.assert_not_called()

    def test_the_budget_starts_at_the_first_request(self):
        """Whatever happened before, the budget covers the fetching and nothing else."""
        klantcontact = make_klantcontact("r1", "Reaction", "2024-10-02T10:00:00Z")
        client = Mock()
        client.klant_contact.retrieve.return_value = klantcontact
        clock = FakeClock()

        with patch("open_inwoner.openklant.conversations.time.monotonic", clock):
            fetcher = self._fetcher(client, timeout=10)
            # The listing this fetcher completes took its own time to come back.
            clock.advance(60)

            klantcontacten, complete = fetcher.retrieve(["r1"])

        self.assertTrue(complete)
        self.assertEqual(klantcontacten, [klantcontact])

    def test_the_budget_is_shared_by_every_request(self):
        """A budget per call would let one conversation spend it over and over."""
        clock = FakeClock()
        client = Mock()

        def _slow_retrieve(uuid, params=None):
            clock.advance(6)
            return make_klantcontact(uuid, "Reaction", "2024-10-02T10:00:00Z")

        client.klant_contact.retrieve.side_effect = _slow_retrieve

        with patch("open_inwoner.openklant.conversations.time.monotonic", clock):
            fetcher = self._fetcher(client, timeout=10)

            first, first_complete = fetcher.retrieve(["r1"])
            # 6 of the 10 seconds are gone, so the second retrieval runs but the
            # third never starts.
            second, second_complete = fetcher.retrieve(["r2", "r3"])

        self.assertTrue(first_complete)
        self.assertEqual(len(first), 1)
        self.assertFalse(second_complete)
        self.assertEqual(len(second), 1)
