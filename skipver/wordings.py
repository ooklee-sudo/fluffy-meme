"""Headline wordings, transcribed from Online Appendix E (Table E1).

Index 0 of each frame is the registered headline. Placeholders:
d = points lost on the last step, L = unrealized loss, g = gap to target,
q = current quality, T = target, r = last result.
"""
import hashlib
import json

LOSS = [
    "The last result reduced quality by {d} points. Unrealized cumulative loss is {L}.",
    "The latest update knocked quality down by {d} points, bringing the unrealized loss total to {L}.",
    "Quality slipped by {d} points after the last update, with cumulative unrealized loss now at {L}.",
    "The most recent change degraded quality by {d} points, pushing total unrealized loss to {L}.",
    "An update just dropped quality by {d} points, leaving the running unrealized loss at {L}.",
    "Quality took a hit of {d} points on the last update, and unrealized loss now totals {L}.",
    "The last update caused a quality decline of {d} points, with {L} in unrealized loss accumulated so far.",
    "A drop of {d} points in quality followed the last update, raising cumulative unrealized loss to {L}.",
    "The service saw quality fall by {d} points after the recent update, totaling {L} in unrealized loss.",
    "Following the last update, quality decreased by {d} points, and unrealized loss now stands at {L}.",
    "The newest update reduced quality by {d} points, with the unrealized loss total reaching {L}.",
    "Quality dropped {d} points on the latest update, accumulating {L} in unrealized loss overall.",
    "The recent update eroded quality by {d} points, bringing total unrealized loss up to {L}.",
    "A quality reduction of {d} points occurred with the last update, with unrealized loss now at {L}.",
    "The last change lowered quality by {d} points, and the cumulative unrealized loss is now {L}.",
    "Quality worsened by {d} points following the latest update, with {L} in unrealized loss so far.",
]

GAIN = [
    "{g} points remain to the target. Current quality {q} / {T}.",
    "Quality is currently {q}, and {g} points separate us from the target.",
    "Current quality stands at {q}; the distance to the target is {g} points.",
    "We are at {q} quality with {g} points still to cover before reaching the target.",
    "Quality reads {q} right now. Another {g} points would reach the target.",
    "The target is {g} points away, and quality currently sits at {q}.",
    "Reaching the target of {T} requires {g} more points; quality is presently {q}.",
    "Present quality: {q}. Distance remaining to the target: {g} points.",
    "Quality has been measured at {q}, leaving {g} points to reach the target.",
    "With quality at {q}, we still need {g} points to hit the target.",
    "Target progress: {g} points left to climb, with quality reported at {q}.",
    "Quality is {q} against a target of {T}, so {g} points remain to be gained.",
    "The service is showing quality of {q}; {g} points are needed to reach the target.",
    "Still ahead of us: {g} points to the target. Quality at this moment is {q}.",
    "Latest quality reading is {q}, which leaves {g} points to cover to the target.",
    "Quality now: {q}. Target: {T}. Points left to gain: {g}.",
]

NEUTRAL = [
    "Current quality {q}. Last result: {r}.",
    "Quality stands at {q}; the last update resulted in {r}.",
    "Current quality reading: {q}. The most recent update came back as {r}.",
    "Quality is now {q}, following an update that ended in {r}.",
    "The service shows quality {q}, with the last update marked {r}.",
    "Quality level: {q}. Last update outcome: {r}.",
    "At present, quality sits at {q}; last update status was {r}.",
    "Reporting quality {q}, last update result {r}.",
    "Quality currently measured as {q}. Previous update concluded with {r}.",
    "The latest quality figure is {q}, and the last update finished as {r}.",
    "Quality now reads {q}; last update attempt returned {r}.",
    "Status check: quality {q}, last update {r}.",
    "Observed quality is {q}, with the most recent update logged as {r}.",
    "Quality metric holds at {q}. Last update returned a result of {r}.",
    "Current state shows quality {q} and a last update of {r}.",
    "Quality today is {q}; the prior update ended with {r}.",
]

WORDINGS = {"loss": LOSS, "gain": GAIN, "neutral": NEUTRAL}
N_WORDINGS = 16

for _name, _lst in WORDINGS.items():
    assert len(_lst) == N_WORDINGS, (_name, len(_lst))


def wordings_sha() -> str:
    """Short content hash of the wording file, logged with every row."""
    blob = json.dumps(WORDINGS, sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()[:12]
