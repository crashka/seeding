#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Load a previously generated seed round bracket and print the evaluation for it.
"""

import sys
import csv

from seed_round import Bracket

def main() -> int:
    """Usage::

      $ python -m seed_eval <nplayers> <nrounds> <filename>

    The input file is expected to be a CSV where each row represents a round in the
    bracket, and the team/matchup designations are specified in groups of four values
    (i.e. (p1, p2) vs. (p3, p4)), with byes (if any) appearing at the end of the row.
    Player "names" are currently expected to be contiguous 1-based integers (1-n).

    See `ray-32-8.csv` and `ray-33-8.csv` as sample input files.
    """
    nplayers  = int(sys.argv[1])
    nrounds   = int(sys.argv[2])
    filename  = sys.argv[3]

    bracket = Bracket(nplayers, nrounds)

    with open(filename, newline='') as f:
        reader = csv.reader(f)
        for rnd, row in enumerate(reader):
            teams = set()
            matchups = set()
            while len(row) >= 4:
                p1, p2, p3, p4 = (int(x) - 1 for x in row[:4])
                team1, team2 = (p1, p2), (p3, p4)
                teams.add(team1)
                teams.add(team2)
                matchups.add((team1, team2))
                del row[:4]
            byes = {int(x) - 1 for x in row}
            bracket.add_byes(rnd, byes)
            bracket.add_teams(rnd, teams)
            bracket.add_matchups(rnd, matchups)

    bracket.evaluate()
    bracket.print()
    return 0

if __name__ == "__main__":
    sys.exit(main())
