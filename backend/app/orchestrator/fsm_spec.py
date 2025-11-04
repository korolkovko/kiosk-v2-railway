# app/orchestrator/fsm_spec.py
# Declarative FSM spec (Python) for kiosk order flow.
# We keep a code-first spec now and will move it to YAML later with the same shape.
#
# What's included:
# - State and Event enums (canonical names)
# - Triplet list (from_state, to_state, trigger_event) -> compiled transitions map
# - Normalization of typos/aliases from your draft (e.g., "AWAITING PAYMENT")
# - Per-state metadata stubs (timeouts, allow_retry) for later config
# - Helper API: next_state, can_transition, is_terminal, state_timeout, is_retry_allowed
# - Spec validation to catch undefined states/events during startup
#
# FSM FLOW: INIT → AWAITING_PAYMENT → AWAITING_PRINTING → AWAITING_KDS → TERMINAL_STATES
# 1. Fiscalization happens first (INIT → AWAITING_PAYMENT)
# 2. Payment processing (AWAITING_PAYMENT → AWAITING_PRINTING)
# 3. Receipt printing (AWAITING_PRINTING → AWAITING_KDS)
# 4. KDS integration (AWAITING_KDS → SENT_TO_KDS/SENT_TO_KDS_FAILED)
#
# IMPORTANT
# - This module is transport-agnostic. The orchestrator will import it and
#   map handler names/timeouts to actual behavior.
# - All comments are in English per your request.

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple, Optional


# ---------- Canonical enums ---------------------------------------------------

class State(str, Enum):
    INIT                     = "INIT"
    AWAITING_PAYMENT         = "AWAITING_PAYMENT"
    AWAITING_PRINTING        = "AWAITING_PRINTING"
    AWAITING_KDS             = "AWAITING_KDS"

    # Terminal / failure / side branches
    CANCELED_BY_USER         = "CANCELED_BY_USER"
    CANCELED_BY_TIMEOUT      = "CANCELED_BY_TIMEOUT"
    UNSUCCESSFUL_PAYMENT     = "UNSUCCESSFUL_PAYMENT"
    PRINTING_FAILED          = "PRINTING_FAILED"
    SENT_TO_KDS              = "SENT_TO_KDS"
    SENT_TO_KDS_FAILED       = "SENT_TO_KDS_FAILED"
    UNSUCCESSFUL_FISCALIZATION = "UNSUCCESSFUL_FISCALIZATION"


class Event(str, Enum):
    # From your table (normalized)
    FISCALIZATION_SUCCEEDED  = "FISCALIZATION_SUCCEEDED"
    FISCALIZATION_FAILED     = "FISCALIZATION_FAILED"

    PAYMENT_SUCCEEDED        = "PAYMENT_SUCCEEDED"
    USER_CANCELED            = "USER_CANCELED"
    INACTIVITY_TIMEOUT       = "INACTIVITY_TIMEOUT"
    PAYMENT_FAILED           = "PAYMENT_FAILED"

    PRINTING_SUCCEEDED       = "PRINTING_SUCCEEDED"
    PRINTING_FAILED_OR_TIMEOUT = "PRINTING_FAILED_OR_TIMEOUT"

    KDS_CONFIRMATION         = "KDS_CONFIRMATION"
    KDS_ERROR_OR_NO_RESPONSE = "KDS_ERROR_OR_NO_RESPONSE"


# ---------- Aliases / normalization for draft typos & spaces ------------------

_STATE_ALIASES: Dict[str, State] = {
    "AWAITING PAYMENT": State.AWAITING_PAYMENT,     # space -> underscore
    "AWAITING KDS": State.AWAITING_KDS,             # space -> underscore
    "PRINTING_FAILD": State.PRINTING_FAILED,        # typo
    "UNSUCCESSFULL_PAYMENT": State.UNSUCCESSFUL_PAYMENT,  # typo (double L)
}

_EVENT_ALIASES: Dict[str, Event] = {
    "PAYMENT_FAILD": Event.PAYMENT_FAILED,               # typo
    "PRINTING_FAILD_OR_TIMEOUT": Event.PRINTING_FAILED_OR_TIMEOUT,  # typo
    "PRINTING_SUCEEDED": Event.PRINTING_SUCCEEDED,       # typo
}

def normalize_state_name(name: str) -> State:
    """Map incoming/legacy state strings to canonical State enum."""
    name = name.strip().upper()
    if name in State.__members__:
        return State[name]
    if name in _STATE_ALIASES:
        return _STATE_ALIASES[name]
    # Also try replacing spaces with underscores as a convenience
    name2 = name.replace(" ", "_")
    if name2 in State.__members__:
        return State[name2]
    raise ValueError(f"Unknown state: {name}")

def normalize_event_name(name: str) -> Event:
    """Map incoming/legacy event strings to canonical Event enum."""
    name = name.strip().upper()
    if name in Event.__members__:
        return Event[name]
    if name in _EVENT_ALIASES:
        return _EVENT_ALIASES[name]
    name2 = name.replace(" ", "_")
    if name2 in Event.__members__:
        return Event[name2]
    raise ValueError(f"Unknown event: {name}")


# ---------- Raw triplets (from | to | trigger) as provided --------------------

# Updated transitions with AWAITING_KDS state integration
_RAW_TRIPLETS: List[Tuple[str, str, str]] = [
    # from               to                         trigger
    ("INIT",            "AWAITING PAYMENT",        "FISCALIZATION_SUCCEEDED"),   # Fiscalization first, then payment
    ("INIT",            "UNSUCCESSFUL_FISCALIZATION", "FISCALIZATION_FAILED"),   # Fiscalization failure

    ("AWAITING_PAYMENT","AWAITING_PRINTING",       "PAYMENT_SUCCEEDED"),
    ("AWAITING_PAYMENT","CANCELED_BY_USER",        "USER_CANCELED"),
    ("AWAITING_PAYMENT","CANCELED_BY_TIMEOUT",     "INACTIVITY_TIMEOUT"),
    ("AWAITING_PAYMENT","UNSUCCESSFULL_PAYMENT",   "PAYMENT_FAILD"),

    # New flow: AWAITING_PRINTING -> AWAITING_KDS -> KDS terminal states
    ("AWAITING_PRINTING","PRINTING_FAILD",         "PRINTING_FAILD_OR_TIMEOUT"),
    ("AWAITING_PRINTING","AWAITING_KDS",           "PRINTING_SUCCEEDED"),
    
    ("AWAITING_KDS",     "SENT_TO_KDS",            "KDS_CONFIRMATION"),
    ("AWAITING_KDS",     "SENT_TO_KDS_FAILED",     "KDS_ERROR_OR_NO_RESPONSE"),
]


# ---------- Compile transitions map ------------------------------------------

# transitions[from_state][event] = to_state
TransitionsMap = Dict[State, Dict[Event, State]]
_transitions: TransitionsMap = {}

for raw_from, raw_to, raw_ev in _RAW_TRIPLETS:
    s_from = normalize_state_name(raw_from)
    s_to   = normalize_state_name(raw_to)
    ev     = normalize_event_name(raw_ev)
    _transitions.setdefault(s_from, {})
    if ev in _transitions[s_from]:
        raise ValueError(f"Duplicate transition for ({s_from}, {ev})")
    _transitions[s_from][ev] = s_to


# ---------- Metadata stubs (to be moved into config later) --------------------

# Default timeouts per state (in seconds).
# Orchestrator should persist deadlines so timers can be recovered after restart.
_state_timeouts: Dict[State, int] = {
    State.AWAITING_PAYMENT: 180,         # inactivity timeout before cancel
    State.AWAITING_PRINTING: 60,         # printing timeout
    State.AWAITING_KDS: 20,               # KDS timeout (fail-fast approach)
}

# Whether user/system is allowed to trigger a 'retry' semantic within a state.
# (This does not define transitions, only a policy bit you can check in API.)
_allow_retry: Dict[State, bool] = {
    State.AWAITING_PAYMENT: True,        # allow retry payment
    State.AWAITING_PRINTING: True,       # allow reprint
    State.AWAITING_KDS: False,            # no retry for KDS (fail-fast)
}


# ---------- Helper API --------------------------------------------------------

def next_state(current: State, event: Event) -> Optional[State]:
    """Return the next state for (current, event) or None if not allowed."""
    return _transitions.get(current, {}).get(event)

def can_transition(current: State, event: Event) -> bool:
    """Check if a transition exists for (current, event)."""
    return event in _transitions.get(current, {})

def valid_events(current: State) -> List[Event]:
    """List allowed events from current state."""
    return list(_transitions.get(current, {}).keys())

def is_terminal(state: State) -> bool:
    """Define terminal states (no outgoing transitions)."""
    return state not in _transitions or len(_transitions[state]) == 0

def state_timeout(state: State) -> Optional[int]:
    """Return advisory timeout (seconds) for a state, if any."""
    return _state_timeouts.get(state)

def is_retry_allowed(state: State) -> bool:
    """Return whether retry is allowed in this state (policy flag)."""
    return _allow_retry.get(state, False)


# ---------- Startup validation ------------------------------------------------

def validate_spec() -> None:
    """
    Validate that the transition graph references only known states/events.
    Call this once on app startup.
    """
    # Check all 'from'/'to' states exist in Enum (already normalized at compile)
    for s_from, edges in _transitions.items():
        if not isinstance(s_from, State):
            raise AssertionError(f"Invalid state type: {s_from}")
        for ev, s_to in edges.items():
            if not isinstance(ev, Event):
                raise AssertionError(f"Invalid event type: {ev}")
            if not isinstance(s_to, State):
                raise AssertionError(f"Invalid state type: {s_to}")

    # Optional: detect dead-ends that are not intended terminal states
    # (We keep it informational only.)
    # Example: warn if AWAITING_PRINTING does not transition to a "DELIVERED"-like state.


# Expose compiled transitions (read-only)
TRANSITIONS: TransitionsMap = _transitions