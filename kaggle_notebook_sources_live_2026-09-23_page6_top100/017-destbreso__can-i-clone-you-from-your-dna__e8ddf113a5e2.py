import hashlib, json

def stream_hash(actions):
    """One line of DNA per episode: the hash of everything the agent did."""
    return hashlib.md5(json.dumps(actions, sort_keys=True).encode()).hexdigest()[:8]

# What the test returns for three real agents (8 episodes each, distinct hashes):
#   agent A: 8 distinct of 8   -> fully reactive or a huge repertoire; not capturable this way
#   agent B: 8 distinct of 8   -> same
#   agent C: 4 distinct of 8   -> a FINITE REPERTOIRE; this is the target
print("distinct streams over 8 episodes: 8 = safe, small = clonable")

# The target's full public history, crawled and hashed: 238 episodes.
repertoire = {
    "stream_01": 70, "stream_02": 36, "stream_03": 36, "stream_04": 24,
    "stream_05": 16, "stream_06": 15, "stream_07": 9,  "stream_08": 6,
    # ... 11 more streams with 1-5 episodes each
}
total, distinct = 238, 19
top6 = sum(sorted(repertoire.values(), reverse=True)[:6])
print(f"{total} episodes -> {distinct} distinct streams")
print(f"top 6 streams cover {top6}/{total} = {top6/total:.0%} of everything it ever played")

import collections, hashlib, json, time, urllib.request

LIST_URL = "https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes"
REPLAY_URL = "https://www.kaggleusercontent.com/episodes/{id}.json"


def _post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def episodes_of(submission_id):
    """Every completed episode the ladder holds for one submission."""
    eps = _post(LIST_URL, {"submissionId": int(submission_id)}).get("episodes", [])
    return sorted((e for e in eps if e.get("state") == "COMPLETED"),
                  key=lambda e: e.get("endTime") or "")


def stream_of(episode, submission_id):
    """The agent's full action stream from one public replay, plus the world."""
    rep = json.loads(urllib.request.urlopen(
        REPLAY_URL.format(id=episode["id"]), timeout=90).read())
    steps = rep["steps"]
    seat = next(i for i, a in enumerate(episode["agents"])
                if a.get("submissionId") == int(submission_id))
    acts = [steps[t][seat].get("action") or {} for t in range(1, len(steps))]
    town = (steps[-1][0].get("observation", {}) or {}).get("town") or {}
    return acts, town.get("unlocked_shops") or [], (rep.get("info") or {}).get("seed")


def repertoire(submission_id, sample=16, pause=0.3):
    """Step 1, the capturability test: distinct full streams over a sample.
    8 of 8 distinct means walk away; a concentrated handful means a target."""
    counts = collections.Counter()
    for e in episodes_of(submission_id)[-sample:]:
        acts, _, _ = stream_of(e, submission_id)
        counts[hashlib.md5(json.dumps(acts, sort_keys=True).encode()).hexdigest()[:8]] += 1
        time.sleep(pause)
    return counts


def branch_point(acts_a, acts_b):
    """Step 2: the first turn two streams disagree names what the rule reads."""
    return next((t for t in range(min(len(acts_a), len(acts_b)))
                 if acts_a[t] != acts_b[t]), None)


def harvest(submission_id, pause=0.3):
    """Step 3: the deduplicated genome, keyed for a world-prefix dispatch.
    Feeding it to a router and validating the result is your half of the work."""
    tapes, keys = {}, collections.defaultdict(list)
    for e in episodes_of(submission_id):
        acts, shops, seed = stream_of(e, submission_id)
        h = hashlib.md5(json.dumps(acts, sort_keys=True).encode()).hexdigest()[:10]
        tapes.setdefault(h, acts)
        keys[tuple(shops[:2])].append(h)
        time.sleep(pause)
    return {"tapes": tapes, "world_index": dict(keys)}


def am_i_clonable(submission_id, sample=16):
    """The self-test: run the capturability diagnosis on YOUR OWN submission
    and get the verdict the harvester would reach about you."""
    dist = repertoire(submission_id, sample=sample)
    n, k = sum(dist.values()), len(dist)
    top = max(dist.values()) if dist else 0
    print(f"{n} episodes sampled, {k} distinct streams, largest cluster {top}")
    if k == n:
        print("VERDICT: not capturable this way. Every episode is a different game;")
        print("there is no finite repertoire to steal. (A larger sample can still revise this.)")
    elif k <= max(2, n // 3):
        print("VERDICT: CLONABLE. A concentrated finite repertoire: a harvester gets")
        print("a working copy of you in an afternoon. The defense section above is for you.")
    else:
        print("VERDICT: borderline. Partial clustering; deepen the sample before relaxing,")
        print("because two episodes prove variation and never fixity.")
    return dist

# The trigger. Test yourself first; whoever you point it at, the verdict is real:
MY_SUBMISSION_ID = None
if MY_SUBMISSION_ID:
    am_i_clonable(MY_SUBMISSION_ID)
else:
    print("set MY_SUBMISSION_ID to your own submission and run the self-test")