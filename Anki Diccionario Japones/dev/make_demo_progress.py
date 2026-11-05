"""Crea una COPIA de un mazo con progreso inventado, solo para probar el panel.

Simula ~14 semanas de estudio (unas 40 palabras nuevas por semana) con
repasos, fallos, algunas difíciles y algunas suspendidas. No toca tu mazo
original.

Uso:
    python dev/make_demo_progress.py collection.anki21 demo.anki21
"""

from __future__ import annotations

import datetime as dt
import random
import shutil
import sqlite3
import sys
import time

DAY = 86400


def main(src: str, dst: str, seed: int = 7) -> None:
    shutil.copy(src, dst)
    db = sqlite3.connect(dst)
    rnd = random.Random(seed)
    now = time.time()

    today = dt.datetime.fromtimestamp(now).replace(hour=0, minute=0, second=0, microsecond=0)
    monday = today - dt.timedelta(days=today.weekday())
    weekly = [38, 44, 41, 47, 22, 45, 49, 43, 40, 46, 35, 48, 44, 26]

    cards = db.execute(
        "select c.id, c.nid from cards c join notes n on n.id = c.nid "
        "where n.sfld not like 'Welcome%' order by c.nid"
    ).fetchall()

    revlog_id = int(now * 1000) - 200 * DAY * 1000
    revlog = []
    idx = 0
    for k, count in enumerate(weekly):
        week_start = monday - dt.timedelta(weeks=len(weekly) - 1 - k)
        days_available = 7 if k < len(weekly) - 1 else max(1, (today - week_start).days + 1)
        for _ in range(count):
            if idx >= len(cards):
                break
            cid, nid = cards[idx]
            idx += 1
            first = week_start + dt.timedelta(days=rnd.randrange(days_available), hours=rnd.randint(8, 21),
                                              minutes=rnd.randint(0, 59))
            first_ts = min(first.timestamp(), now - 600)
            age = (now - first_ts) / DAY

            r = rnd.random()
            matured_ts = None
            if age >= 40:
                state = "mature" if r < 0.88 else ("young" if r < 0.97 else "learning")
            elif age >= 25:
                state = "mature" if r < 0.45 else ("young" if r < 0.95 else "learning")
            elif age >= 7:
                state = "young" if r < 0.85 else "learning"
            else:
                state = "learning" if r < 0.6 else "young"

            if state == "mature":
                ivl = rnd.randint(21, max(22, min(int(age * 1.3), 160)))
                matured_ts = first_ts + rnd.uniform(24, min(38, age - 0.5)) * DAY
                ctype, queue = 2, 2
            elif state == "young":
                ivl = rnd.randint(1, max(1, min(20, int(age * 0.7))))
                ctype, queue = 2, 2
            else:
                ivl = 0
                ctype, queue = (3 if age > 10 else 1), 1

            lr = rnd.random()
            lapses = 0 if lr < 0.7 else 1 if lr < 0.88 else 2 if lr < 0.95 else rnd.randint(3, 5)
            reps = 3 + int(age ** 0.5) + lapses * 2

            db.execute("update cards set type=?, queue=?, ivl=?, lapses=?, reps=? where id=?",
                       (ctype, queue, ivl, lapses, reps, cid))
            revlog_id += 1
            revlog.append((int(first_ts * 1000), cid, -1, 3, 1, 0, 2500, 6000, 0))
            if matured_ts:
                revlog.append((int(matured_ts * 1000) + idx, cid, -1, 3, max(ivl, 21), 14, 2500, 4000, 1))

    # Algunas palabras difíciles (sanguijuelas) y algunas suspendidas
    studied = [c for c in cards[:idx]]
    for cid, nid in rnd.sample(studied[:400], 7):
        db.execute("update cards set lapses=?, type=3, queue=1, ivl=0 where id=?", (rnd.randint(8, 12), cid))
        db.execute("update notes set tags=' leech ' where id=?", (nid,))
    for cid, _ in rnd.sample(studied[:300], 9):
        db.execute("update cards set queue=-1 where id=?", (cid,))

    db.executemany("insert or ignore into revlog (id, cid, usn, ease, ivl, lastIvl, factor, time, type) "
                   "values (?,?,?,?,?,?,?,?,?)", revlog)
    db.commit()
    print(f"Copia con progreso de ejemplo: {dst} ({idx} palabras empezadas)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
