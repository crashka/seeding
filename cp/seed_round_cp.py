#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Solve the seeding round problem using Constraint Programming (CP).  In particular, we
are using the cp-sat library from Google's OR Tools.

To Do:

- Solver optimizations for performance
- Different modeling constraints for performance
"""

import sys

from ortools.sat.python import cp_model

from seed_round import Bracket

def build_bracket(nplayers: int, nrounds: int) -> list:
    """Attempt to build a bracket with the specified configuration.  Return ``None`` if
    solver is unable to come up with a solution given the specified parameters and/or
    bounds.

    If the number of players is not divisible by 4, then "ghost" players are created to
    round out the field to the next higher multiple of 4.  Ghost players will always sit
    together, along with the bye player(s) for the round.

    Constraints:

    1. Each table seats exactly 4 players (including ghost players) in every round

    2. Each player (including ghost players) sits at exactly one table in every round

    3. Pairs of players may not sit at the same table in more than one round (except for
       ghost-ghost pairs, see next constraint)

    4. All ghost players (if any) must sit at the same table in every round (we'll make it
       the last table, for simplicity)
    """
    nbyes       = nplayers % 4
    nghosts     = (4 - nbyes) % 4
    tplayers    = nplayers + nghosts
    ntables     = tplayers // 4
    assert tplayers % 4 == 0

    players     = range(nplayers)
    rounds      = range(nrounds)
    tables      = range(ntables)
    all_players = range(tplayers)  # includes ghosts
    ghosts      = all_players[nplayers:]

    model = cp_model.CpModel()

    seats = {}
    for p in all_players:
        for r in rounds:
            for t in tables:
                seats[(p, r, t)] = model.new_bool_var(f'seat_p{p}_r{r}_t{t}')

    # Contraint #1 - for every round, each table seats 4 players
    for r in rounds:
        for t in tables:
            model.add(sum(seats[(p, r, t)] for p in all_players) == 4)

    # Contraint #2 - every player sits at one table per round
    for p in all_players:
        for r in rounds:
            model.add(sum(seats[(p, r, t)] for t in tables) == 1)

    # Contraint #3 - every pair of players meets no more than once across all rounds
    # (except ghost-ghost)
    for p1 in all_players:
        for p2 in all_players:
            if p2 <= p1:
                continue
            if p1 in ghosts and p2 in ghosts:
                continue
            mtgs = []
            for r in rounds:
                for t in tables:
                    mtg = model.new_bool_var(f'mtg_p{p1}_p{p2}_r{r}_t{t}')
                    model.add_multiplication_equality(mtg, [seats[(p1, r, t)], seats[(p2, r, t)]])
                    mtgs.append(mtg)
            model.add(sum(mtgs) < 2)

    # Constraint #4 - ghost players all sit at the last table in every round (along with
    # player(s) getting a bye)
    for g in ghosts:
        for r in rounds:
            model.add(seats[(g, r, ntables - 1)] == 1)

    solver = cp_model.CpSolver()
    status = solver.solve(model)
    print(f"Status: {status} ({solver.status_name(status)})", file=sys.stderr)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None

    bracket = []
    for r in rounds:
        bracket.append([])
        for t in tables:
            # only register real players; if the number of players is less than 4 (after
            # ignoring ghosts), that means they are getting byes for the round--this can
            # only happen for the last table (see `validate_bracket()`)
            bracket[-1].append([p for p in players if solver.value(seats[(p, r, t)])])

    if not validate_bracket(bracket, nplayers, nrounds):
        raise RuntimeError("Generated bracket fails validation")

    print("\nSolver Stats", file=sys.stderr)
    print(f"- Conflicts : {solver.num_conflicts}", file=sys.stderr)
    print(f"- Branches  : {solver.num_branches}", file=sys.stderr)
    print(f"- Wall time : {solver.wall_time:.2f} secs", file=sys.stderr)
    return bracket

def validate_bracket(bracket_in: list, nplayers: int, nrounds: int) -> bool:
    """Return ``True`` if bracket is correct (i.e. all intended constraints met),
    ``False`` otherwise.
    """
    assert nrounds == len(bracket_in)
    val_brkt = Bracket(nplayers, nrounds)

    for r, round in enumerate(bracket_in):
        byes = set()
        teams = set()
        matchups = set()
        for t, table in enumerate(round):
            if len(table) < 4:
                assert t == len(round) - 1
                byes.update(table)
                break
            p1, p2, p3, p4 = table
            team1, team2 = (p1, p2), (p3, p4)
            teams.add(team1)
            teams.add(team2)
            matchups.add((team1, team2))

        val_brkt.add_byes(r, byes)
        val_brkt.add_teams(r, teams)
        val_brkt.add_matchups(r, matchups)

    val_brkt.evaluate()
    return val_brkt.optimal()

def print_bracket(bracket: list) -> None:
    """Print human-readable representation of the generated backed (internal format).
    """
    for r, round in enumerate(bracket):
        print(f"\nRound {r}:")
        for t, table in enumerate(round):
            if len(table) < 4:
                print(f"  Byes: {table}")
            else:
                print(f"  Table {t}: {table}")

def print_bracket_csv(bracket: list) -> None:
    """Print CSV for generated bracket, compatible with input format expected by
    ``seed_eval``.
    """
    for round in bracket:
        print(','.join([str(player + 1) for table in round for player in table]))

########
# main #
########

def main() -> int:
    """Usage::

      $ python -m seed_round_cp <nplayers> <nrounds> [<csvout>]
    """
    nplayers = int(sys.argv[1])
    nrounds  = int(sys.argv[2])
    csvout   = None
    if len(sys.argv) > 3:
        csvout = bool(sys.argv[3])
        if len(sys.argv) > 4:
            print(f"Invalid arg(s): {' '.join(sys.argv[4:])}", file=sys.stderr)
            return 1

    bracket = build_bracket(nplayers, nrounds)
    if not bracket:
        print("Unable to build bracket", file=sys.stderr)
        return 1

    if csvout:
        print_bracket_csv(bracket)
    else:
        print_bracket(bracket)
    return 0

if __name__ == "__main__":
    sys.exit(main())
