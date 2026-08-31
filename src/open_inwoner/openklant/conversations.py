"""Building conversations out of the klantcontacten a listing returns.

A question and the reactions that follow it are separate klantcontacten, tied
together by onderwerpobjecten: a reaction's onderwerpobject points, through
`wasKlantcontact`, at whatever it replies to. An external service may point it at
the previous reaction rather than at the original question, so a conversation is a
chain and the question is its root.

The partij-filtered listing does not always return the whole chain. A reaction
registered without the citizen as a betrokkene is missing from it, and no filter on
`/klantcontacten` can bring it in, so the missing klantcontacten have to be fetched
one at a time. `ConversationGraph.build` is that logic, and it reaches the API only
through an injected `ConversationFetcher`, so the walking can be exercised without a
client.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Collection, Iterable
from dataclasses import dataclass, field
from typing import Literal, Protocol, TypeVar

import glom
import structlog
from openklant_client import OpenKlantClient
from openklant_client.exceptions import NotFound as OK2NotFound
from openklant_client.types.resources.klant_contact import KlantContact
from openklant_client.types.resources.onderwerp_object import (
    OnderwerpObject,
    OnderwerpobjectIdentificatorListParams,
)

from open_inwoner.utils.concurrency import TimedParallel

logger = structlog.stdlib.get_logger(__name__)

T = TypeVar("T")


# The listing and the individual retrievals have to expand the same relations: a
# klantcontact fetched to complete a conversation is merged into the same graph as the
# listing's rows, and anything missing from its `_expand` would cost a request per
# klantcontact to fetch back.
CONVERSATION_EXPAND: list[
    Literal[
        "gingOverOnderwerpobjecten",
        "hadBetrokkenen",
        "hadBetrokkenen.wasPartij",
        "leiddeTotInterneTaken",
    ]
] = [
    "leiddeTotInterneTaken",
    "gingOverOnderwerpobjecten",
    "hadBetrokkenen",
    "hadBetrokkenen.wasPartij",
]

# Completing a conversation is IO-bound, so the worker count is not tied to CPU count.
# Kept modest: this fans out over one klantinteracties API, which is the constrained
# side.
DEFAULT_WORKERS = 8

# Onderwerpobjecten are asked for one klantcontact at a time, so the maximum page size
# normally makes the answer a single request. Every page is still followed: a
# conversation must not lose its newest replies to a page boundary.
_ONDERWERP_OBJECTEN_PAGE_SIZE = 500


def expanded_onderwerp_objecten(klantcontact: KlantContact) -> list[OnderwerpObject]:
    """A klantcontact's onderwerpobjecten as they arrived in its `_expand`."""
    return glom.glom(
        klantcontact,
        glom.Coalesce("_expand.gingOverOnderwerpobjecten", default=[]),
    )


def parent_klantcontact_uuid(
    klantcontact: KlantContact, onderwerp_objecten: Iterable[OnderwerpObject]
) -> str | None:
    """Return the klantcontact this one replies to, if it replies to one.

    A klantcontact can carry several onderwerpobjecten, of which only the ones with a
    `wasKlantcontact` link it to another klantcontact; the rest tie it to a zaak. Any
    such link makes it a reaction, so a reaction that also references a zaak is not
    mistaken for a question.
    """
    parent_uuids = [
        onderwerp_object["wasKlantcontact"]["uuid"]
        for onderwerp_object in onderwerp_objecten
        if onderwerp_object.get("wasKlantcontact")
    ]

    if not parent_uuids:
        return None

    if len(parent_uuids) > 1:
        # Allowed by the data model, but no known registration produces it, so
        # picking the first is a guess worth knowing about.
        logger.warning(
            "Klantcontact replies to more than one klantcontact; using the first",
            klantcontact_uuid=klantcontact["uuid"],
        )

    return parent_uuids[0]


def parent_uuid_from_expand(klantcontact: KlantContact) -> str | None:
    """Read the parent off the klantcontact alone, issuing no requests."""
    return parent_klantcontact_uuid(
        klantcontact, expanded_onderwerp_objecten(klantcontact)
    )


class ConversationFetcher(Protocol):
    """The two requests completing a conversation needs.

    Both report what they found together with whether they found all of it, so that a
    conversation that could not be completed is shown in part rather than failing the
    page.
    """

    def retrieve(self, uuids: Collection[str]) -> tuple[list[KlantContact], bool]:
        """Retrieve klantcontacten by uuid, expanded as `CONVERSATION_EXPAND` says."""
        ...

    def replies_to(self, uuids: Collection[str]) -> tuple[set[str], bool]:
        """Return the uuids of the klantcontacten replying to any of these."""
        ...


@dataclass
class ConversationGraph:
    """Klantcontacten linked into conversations by their onderwerpobjecten.

    A reaction is registered as a klantcontact whose onderwerpobject points at the
    klantcontact it replies to. An external service may point it at the previous
    reaction rather than at the original question, so a conversation is a chain and
    the question is its root.

    `build` is how a listing becomes one of these. Everything it fetches goes through
    an injected `ConversationFetcher`, so the graph itself holds no client and the
    passes below can be exercised against a stand-in that answers from a dict.
    """

    nodes: dict[str, KlantContact] = field(default_factory=dict)
    parent_of: dict[str, str] = field(default_factory=dict)
    children_of: dict[str, list[str]] = field(default_factory=dict)

    @classmethod
    def build(
        cls,
        klantcontacten: Iterable[KlantContact],
        fetcher: ConversationFetcher,
        parent_uuid_for: Callable[[KlantContact], str | None] = parent_uuid_from_expand,
    ) -> tuple[ConversationGraph, bool]:
        """Merge a list of klantcontacten into the graph, fetching what the listing cannot return.

        A reaction registered without the citizen as a betrokkene is not in the
        partij-filtered listing, and no filter on `/klantcontacten` can bring it in.
        Two passes cover the two shapes that leaves: `_repair_missing_parents` works
        backwards from reactions pointing at a klantcontact we do not have,
        `_walk_for_hidden_replies` forwards from the klantcontacten we do.
        """
        graph = cls()
        graph._merge(klantcontacten, parent_uuid_for)

        repaired = graph._repair_missing_parents(fetcher, parent_uuid_for)
        walked = graph._walk_for_hidden_replies(fetcher, parent_uuid_for)

        return graph, repaired and walked

    @property
    def root_uuids(self) -> list[str]:
        """The klantcontacten that reply to nothing, in the order they came in."""
        return [
            klantcontact_uuid
            for klantcontact_uuid in self.nodes
            if klantcontact_uuid not in self.parent_of
        ]

    @property
    def orphan_uuids(self) -> list[str]:
        """Klantcontacten whose parent is missing, so their root is unknown."""
        return [
            klantcontact_uuid
            for klantcontact_uuid, parent_uuid in self.parent_of.items()
            if parent_uuid not in self.nodes
        ]

    @property
    def missing_parent_uuids(self) -> set[str]:
        """The klantcontacten replied to that the graph does not have."""
        return {
            parent_uuid
            for parent_uuid in self.parent_of.values()
            if parent_uuid not in self.nodes
        }

    def add(self, klantcontact: KlantContact, parent_uuid: str | None) -> None:
        """Add a klantcontact, leaving one already in the graph alone.

        The repair and walk passes can arrive at a klantcontact the listing already
        returned; adding it again would list it among its parent's children twice, and
        so report the same reaction twice.
        """
        klantcontact_uuid = klantcontact["uuid"]
        if klantcontact_uuid in self.nodes:
            return

        self.nodes[klantcontact_uuid] = klantcontact

        if parent_uuid:
            self.parent_of[klantcontact_uuid] = parent_uuid
            self.children_of.setdefault(parent_uuid, []).append(klantcontact_uuid)

    def descendants(self, root_uuid: str) -> list[str]:
        """Every klantcontact replying to the root, directly or via a reaction.

        The visited set is what makes this terminate: a klantcontact is collected at
        most once, so a chain that refers back to itself ends the walk rather than
        looping.
        """
        seen = {root_uuid}
        collected: list[str] = []
        frontier = [root_uuid]

        while frontier:
            next_frontier = []
            for klantcontact_uuid in frontier:
                for child_uuid in self.children_of.get(klantcontact_uuid, []):
                    if child_uuid in seen:
                        continue
                    seen.add(child_uuid)
                    collected.append(child_uuid)
                    next_frontier.append(child_uuid)
            frontier = next_frontier

        return collected

    def _merge(
        self,
        klantcontacten: Iterable[KlantContact],
        parent_uuid_for: Callable[[KlantContact], str | None],
    ) -> None:
        """Add klantcontacten, linking each to what it replies to."""
        for klantcontact in klantcontacten:
            self.add(klantcontact, parent_uuid_for(klantcontact))

    def _repair_missing_parents(
        self,
        fetcher: ConversationFetcher,
        parent_uuid_for: Callable[[KlantContact], str | None],
    ) -> bool:
        """Retrieve the klantcontacten replied to that the listing did not return.

        This is the reaction hidden mid-chain: a later reaction points at it, which is
        how we know it exists, so it costs a retrieval only when it actually occurs. A
        repaired klantcontact can itself reply to one we do not have, hence the loop;
        `attempted` is what ends it, by giving each uuid a single try.
        """
        attempted: set[str] = set()

        while missing := self.missing_parent_uuids - attempted:
            attempted |= missing
            klantcontacten, complete = fetcher.retrieve(missing)
            self._merge(klantcontacten, parent_uuid_for)

            if not complete:
                return False

        return True

    def _walk_for_hidden_replies(
        self,
        fetcher: ConversationFetcher,
        parent_uuid_for: Callable[[KlantContact], str | None],
    ) -> bool:
        """Discover the klantcontacten that reply to ones we have but are not listed.

        This is the reaction at the end of a chain: nothing points at it, so asking is
        the only way to learn that it exists. That makes it the recurring cost of the
        whole exercise, a request per known klantcontact, and also the reason the
        exercise is worth it, because the newest reaction is the one the citizen is
        waiting for.

        Walking from every klantcontact rather than only from the ends of chains is
        deliberate: answers written here link straight to the question, so a
        conversation can be a star rather than a chain, and a klantcontact with known
        replies can still have an unknown one.
        """
        frontier = set(self.nodes)

        while frontier:
            reply_uuids, listed = fetcher.replies_to(frontier)
            hidden = reply_uuids - self.nodes.keys()

            if not hidden:
                return listed

            klantcontacten, retrieved = fetcher.retrieve(hidden)
            self._merge(klantcontacten, parent_uuid_for)

            if not (listed and retrieved):
                return False

            # Only what we just discovered can have replies we have not asked about,
            # so a klantcontact enters the frontier at most once. That is what ends
            # this loop: the work is linear in the size of the conversation, and the
            # budget bounds it in time.
            frontier = {klantcontact["uuid"] for klantcontact in klantcontacten}

        return True


class OpenKlantConversationFetcher:
    """Completes conversations against the klantinteracties API.

    This is a class rather than a pair of functions in order to hold one time budget
    for the whole of completing a conversation. Repairing and walking each issue
    several rounds of requests, and they have to share a single deadline: a budget per
    call would let a conversation spend it over and over, and the citizen would wait
    for as long as it took. Holding it here also keeps it out of the resolver, which
    then has nothing to say about time.

    Build one per resolution. The budget starts at the first request rather than at
    construction, so it covers the fetching and nothing else, whatever happened
    between building this and putting it to work.
    """

    def __init__(
        self,
        client_factory: Callable[[], OpenKlantClient],
        *,
        timeout: float,
        max_workers: int | None = None,
    ):
        self._client_factory = client_factory
        self._max_workers = max_workers or DEFAULT_WORKERS
        self._timeout = timeout
        self._started_deadline: float | None = None

    @property
    def _deadline(self) -> float:
        """The moment the budget runs out, counted from the first request."""
        if self._started_deadline is None:
            self._started_deadline = time.monotonic() + self._timeout
        return self._started_deadline

    def retrieve(self, uuids: Collection[str]) -> tuple[list[KlantContact], bool]:
        """Retrieve klantcontacten by uuid, expanded the way the listing expands them.

        `retrieve` takes the same `expand`, so one fetched here is ready to merge into
        the graph and costs no follow-up request for its onderwerpobjecten or interne
        taken.
        """

        def _retrieve(
            klantcontact_uuid: str, client: OpenKlantClient
        ) -> KlantContact | None:
            try:
                return client.klant_contact.retrieve(
                    klantcontact_uuid, params={"expand": CONVERSATION_EXPAND}
                )
            except OK2NotFound:
                # Something points at a klantcontact that is not there. There is
                # nothing to fetch and retrying next page view would not help, so this
                # is as complete as the conversation gets, not an incomplete result.
                logger.warning(
                    "Klantcontact refers to a klantcontact that does not exist",
                    klantcontact_uuid=klantcontact_uuid,
                )
                return None

        retrieved, complete = self._fetch_in_parallel(
            uuids, _retrieve, name="retrieve_klantcontacten"
        )
        return [
            klantcontact for klantcontact in retrieved if klantcontact is not None
        ], complete

    def replies_to(self, uuids: Collection[str]) -> tuple[set[str], bool]:
        """Ask which klantcontacten reply to each of these.

        `/klantcontacten` cannot express "everything replying to X", so this goes the
        long way round, through the onderwerpobjecten that carry the link.
        """

        def _replies(klantcontact_uuid: str, client: OpenKlantClient) -> list[str]:
            params: OnderwerpobjectIdentificatorListParams = {
                "wasKlantcontact__uuid": klantcontact_uuid,
                "pageSize": _ONDERWERP_OBJECTEN_PAGE_SIZE,
            }
            # `list_iter` requests each page as it is consumed, so the comprehension
            # is what does the fetching, inside the error handling and the budget the
            # caller wraps this in.
            return [
                onderwerp_object["klantcontact"]["uuid"]
                for onderwerp_object in client.onderwerp_object.list_iter(params=params)
                if onderwerp_object.get("klantcontact")
            ]

        replies, complete = self._fetch_in_parallel(
            uuids, _replies, name="reply_uuids_for_klantcontacten"
        )
        return {
            reply_uuid for reply_uuids in replies for reply_uuid in reply_uuids
        }, complete

    def _fetch_in_parallel(
        self,
        uuids: Collection[str],
        fetch: Callable[[str, OpenKlantClient], T],
        name: str,
    ) -> tuple[list[T], bool]:
        """Run `fetch` for every uuid in parallel, and say whether all of them ran.

        Each worker gets its own client, built here rather than in the worker:
        `requests.Session` is not thread safe, and building one reads configuration
        that a worker thread cannot see uncommitted writes to.

        Whatever does not finish inside the remaining budget is reported rather than
        raised, so the caller can show the conversation in part and say so.
        """
        if not uuids:
            return [], True

        deadline = self._deadline
        budget = deadline - time.monotonic()
        if budget <= 0:
            return [], False

        fetched: list[T] = []
        complete = True

        if self._max_workers == 1:
            # A pool of one would add a thread and a hand-off for no concurrency at
            # all. Running here also keeps the requests on the calling thread, which
            # is what lets the VCR tests record and replay them.
            client = self._client_factory()
            for klantcontact_uuid in uuids:
                if time.monotonic() >= deadline:
                    logger.warning(
                        "Ran out of time completing conversations", name=name
                    )
                    return fetched, False
                try:
                    fetched.append(fetch(klantcontact_uuid, client))
                except Exception:
                    logger.exception(
                        "Failed to fetch part of a conversation",
                        klantcontact_uuid=klantcontact_uuid,
                    )
                    complete = False

            return fetched, complete

        with TimedParallel(max_workers=self._max_workers, name=name) as executor:
            future_to_uuid = {
                executor.submit(
                    fetch, klantcontact_uuid, self._client_factory()
                ): klantcontact_uuid
                for klantcontact_uuid in uuids
            }
            outcome = executor.as_completed(future_to_uuid, cancel_after=budget)
            for future in outcome:
                try:
                    fetched.append(future.result())
                except BaseException:
                    logger.exception(
                        "Failed to fetch part of a conversation",
                        klantcontact_uuid=future_to_uuid[future],
                    )
                    complete = False

        if outcome.has_cancelled_futures:
            logger.warning(
                "Ran out of time completing conversations",
                name=name,
                cancelled=len(outcome.cancelled_futures),
            )
            complete = False

        return fetched, complete
