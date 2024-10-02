#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Solve the seeding round problem using Constraint Programming (CP).  In particular, we
are using the cp-sat library from Google's OR Tools.

To Do:

- Add/adjust constraints for bye players (N mod 4 != 0)
"""

import sys

from ortools.sat.python import cp_model

from seed_round import Bracket

def build_bracket(nplayers: int, nrounds: int) -> list:
    """Attempt to build a bracket with the specified parameters.  Return ``None`` if
    solver is unable to come up with a solution within the specified bounds.

    Constraints:
    
    1. Each table has to sit exactly 4 players in each round (including bye players)

    2. Each player (including bye players) sits at exactly one table in each round

    3. Pair of players may not sit at the same table in more than one round (except for
    bye players)

    4. Bye players (if any) must all sit at the same table in every round
    """
    assert nplayers % 4 == 0, "Only multiples of 4 currently supported"
    ntables = nplayers // 4
    
    players = range(nplayers)
    rounds  = range(nrounds)
    tables  = range(ntables)

    model = cp_model.CpModel()
    
    seats = {}
    for p in players:
        for r in rounds:
            for t in tables:
                seats[(p, r, t)] = model.new_bool_var(f'seat_p{p}_r{r}_t{t}')

    # Contraint #1
    for r in rounds:
        for t in tables:
            model.add(sum(seats[(p, r, t)] for p in players) == 4)

    # Contraint #2
    for p in players:
        for r in rounds:
            model.add_exactly_one(seats[(p, r, t)] for t in tables)

    # Contraint #3
    for p1 in players:
        for p2 in players:
            if p2 <= p1:
                continue
            mtgs = []
            for t in tables:
                for r in rounds:
                    mtg = model.new_bool_var(f'mtg_p1{p1}_p2{p2}_r{r}_t{t}')
                    model.add_multiplication_equality(mtg, [seats[(p1, r, t)], seats[(p2, r, t)]])
                    mtgs.append(mtg)
            model.add(sum(mtgs) < 2)

    # Constraint #4
    pass  # coming soon...

    solver = cp_model.CpSolver()
    status = solver.solve(model)
    print(f"Status: {status} ({solver.status_name(status)})")

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None

    bracket = []
    for r in rounds:
        bracket.append([])
        for t in tables:
            bracket[-1].append([p for p in players if solver.value(seats[(p, r, t)])])

    if not validate_bracket(bracket, nplayers, nrounds):
        raise RuntimeError("Generated bracket fails validation")

    print("\nStatistics")
    print(f"- conflicts : {solver.num_conflicts}")
    print(f"- branches  : {solver.num_branches}")
    print(f"- wall time : {solver.wall_time:.2f} secs")
    return bracket

def validate_bracket(bracket_in: list, nplayers: int, nrounds: int) -> bool:
    """Return ``True`` if bracket is correct (i.e. all intended constraints met),
    ``False`` otherwise.
    """
    assert nrounds == len(bracket_in)
    val_brkt = Bracket(nplayers, nrounds)

    for r, round in enumerate(bracket_in):
        teams = set()
        matchups = set()
        for t, table in enumerate(round):
            p1, p2, p3, p4 = table
            team1, team2 = (p1, p2), (p3, p4)
            teams.add(team1)
            teams.add(team2)
            matchups.add((team1, team2))

        byes = set()
        val_brkt.add_byes(r, byes)
        val_brkt.add_teams(r, teams)
        val_brkt.add_matchups(r, matchups)

    val_brkt.evaluate()
    return val_brkt.optimal()

def print_bracket(bracket: list) -> None:
    """Print (to stdout) human-readable representation of the generated backed (internal
    format).
    """
    for r, round in enumerate(bracket):
        print(f"\nRound {r}:")
        for t, table in enumerate(round):
            print(f"  Table {t}: {table}")

########
# main #
########

def main() -> int:
    """Usage::

      $ python -m seed_round_cp <nplayers> <nrounds>
    """
    nplayers  = int(sys.argv[1])
    nrounds   = int(sys.argv[2])
    if len(sys.argv) > 3:
        print(f"Invalid arg(s): {' '.join(sys.argv[3:])}")
        return 1

    bracket = build_bracket(nplayers, nrounds)
    if not bracket:
        print(f"Unable to build bracket")
        return 1

    print_bracket(bracket)
    return 0

if __name__ == "__main__":
    sys.exit(main())
