#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Generate the matchups for the "seeding round" of a card-playing tournament (or any game
consisting of two-player teams competing head-to-head).  The seeding "round" (misnomer) is
actually a truncated round-robin tournament, with a predetermined number of rounds, in
which players switch partners for every round, and the players are ranked by best overall
individual performance.

This module implements a brute force approach, wherein we specify constraints and/or
thresholds for the number and type of interactions allowed between players across the
rounds, and generate random picks for bye, team, and match that conform.  We then define
evaluation functions that indicate the actual levels of repeated interactions and/or
uniqueness of experience (e.g. in second-level interactions).  We can thus generate a
number of conforming brackets and choose the one that demonstrates the best metrics
(though it will almost certainly be suboptimal).
"""

from enum import Enum
from numbers import Number
from statistics import mean, stdev
import random
import sys

##################
# module library #
##################

NPLAYERS = 4

# type aliases
Player   = int
Byes     = set[Player]
Team     = tuple[Player, Player]
Matchup  = tuple[Team, Team]

class PlayerData(Enum):
    """Statistics for evaluating brackets.
    """
    DIST_PARTS   = "Distinct Partners"
    DIST_OPPS    = "Distinct Opponents"
    DIST_INTS    = "Distinct Players (any role)"
    DIST_PARTS_2 = "Distinct 2nd-level Partners"
    DIST_OPPS_2  = "Distinct 2nd-level Opponents"
    DIST_INTS_2  = "Distinct 2nd-level Players (any role)"
    MEAN_PARTS_2 = "Mean 2nd-level Partnerships"
    MEAN_OPPS_2  = "Mean 2nd-level Oppositions"
    MEAN_INTS_2  = "Mean 2nd-level Interactions (any)"
    MIN_PARTS_2  = "Minimum 2nd-level Partnerships"
    MIN_OPPS_2   = "Minimum 2nd-level Oppositions"
    MIN_INTS_2   = "Minimum 2nd-level Interactions (any)"
    MAX_PARTS_2  = "Maximum 2nd-level Partnerships"
    MAX_OPPS_2   = "Maximum 2nd-level Oppositions"
    MAX_INTS_2   = "Maximum 2nd-level Interactions (any)"

FLOAT_PREC = 2

def round_val(val: Number, prec: int = FLOAT_PREC) -> Number:
    """Provide the appropriate level of rounding for a stat value (does not change the
    number type); passthrough for non-numeric types (e.g. bool or str).
    """
    if isinstance(val, float):
        return round(val, prec)
    return val

class Bracket:
    """Represents a possible bracket.
    """
    nplayers:  int
    nrounds:   int

    # numbers for each round
    nbyes:     int
    nseats:    int
    nteams:    int
    nmatchups: int

    # keeping track of rounds
    rnd_byes:     list[Byes]
    rnd_teams:    list[set[Team]]
    rnd_matchups: list[set[Matchup]]

    # keeping track of history across rounds (note that this representation of bye and
    # partner histories depend on the assertion of more rounds than players)
    bye_hist:  set[Player]        # set of players
    part_hist: list[set[Player]]  # indexed by player; value is set of partners
    opp_hist:  list[list[int]]    # indexed by player, opp; value is count

    # stats/evaluation stuff
    stats:       dict[PlayerData, list[Number]]  # list contains [min, max, mean, stdev]
    retry_team:  list[list[int]]  # indexed by round; value is list of team_idx
    retry_match: list[list[int]]  # indexed by round; value is list of match_idx

    def __init__(self, nplayers: int, nrounds: int):
        # this assumption is needed for logic in `pick_teams()`
        assert nplayers > nrounds

        self.nplayers     = nplayers
        self.nrounds      = nrounds
        self.nbyes        = self.nplayers % NPLAYERS
        self.nseats       = self.nplayers - self.nbyes
        self.nteams       = self.nseats // 2
        self.nmatchups    = self.nteams // 2

        self.rnd_byes     = []
        self.rnd_teams    = []
        self.rnd_matchups = []

        self.bye_hist     = set()
        self.part_hist    = [set() for _ in range(self.nplayers)]
        self.opp_hist     = [[0] * self.nplayers for _ in range(self.nplayers)]

        self.stats        = {}
        self.retry_team   = [list() for _ in range(self.nrounds)]
        self.retry_match  = [list() for _ in range(self.nrounds)]

    def pick_byes(self, rnd: int) -> Byes:
        """Pick players that will get a bye this round; we just hardwire the selection to
        be sequential across rounds, to assure evenness.
        """
        start = rnd * self.nbyes
        byes = {x % self.nplayers for x in range(start, start + self.nbyes)}
        assert len(byes) == self.nbyes
        assert not (self.bye_hist & byes)

        self.bye_hist |= byes
        self.rnd_byes.append(byes)
        return byes

    def pick_teams(self, rnd: int, byes: Byes) -> set[Team]:
        """Pick teams for the current round; we avoid picking previous partners, retrying
        the selection process if no qualifying candidates remain.
        """
        teams = set()
        all_players = range(self.nplayers)
        rnd_players = set(all_players) - byes
        assert len(rnd_players) == self.nseats
        # pick partners at random, given that we don't have some kind of smart rotational
        # algorithm for this; we outright exclude previous partners (since we don't have
        # to try and minimize partnerships, since we are asserting more players than
        # rounds)
        for _ in range(10):
            available = rnd_players.copy()
            while available:
                player = random.choice(list(available))
                available.remove(player)
                if available <= self.part_hist[player]:
                    self.retry_team[rnd].append(len(teams))
                    #print(f"Retry picking teams (round {rnd}, team idx {len(teams)})")
                    break
                picklist = list(available - self.part_hist[player])
                partner = random.choice(picklist)
                available.remove(partner)
                teams.add((player, partner))
            if len(teams) < self.nteams:
                teams = set()
                continue
            break
        if len(teams) < self.nteams:
            self.print_retries()
            team_idx = self.retry_team[rnd][-1]
            raise RuntimeError(f"Unable to pick teams (round {rnd}, team idx {team_idx})")
        assert len(teams) % 2 == 0

        for team in teams:
            p1, p2 = team
            self.part_hist[p1].add(p2)
            self.part_hist[p2].add(p1)
        self.rnd_teams.append(teams)
        return teams

    def pick_matchups(self, rnd: int, teams: set[Team]) -> set[Matchup]:
        """Pick matchups for the current round; we avoid picking opposing teams with
        previous partners for either player, and set a (currently suboptimal) threshold
        for maximum times an opposing player is seen.
        """
        OPP_THRESH = 2
        matchups = set()
        for _ in range(100):
            available = teams.copy()
            while available:
                team = random.choice(list(available))
                available.remove(team)
                disqual_part = set()
                disqual_opp = set()
                for player in team:
                    for opp in available:
                        if set(opp) & self.part_hist[player]:
                            disqual_part.add(opp)
                        if (self.opp_hist[player][opp[0]] >= OPP_THRESH or
                            self.opp_hist[player][opp[1]] >= OPP_THRESH):
                            disqual_opp.add(opp)
                if available <= disqual_part | disqual_opp:
                    self.retry_match[rnd].append(len(matchups))
                    #print(f"Retry picking matchup (round {rnd}, match idx {len(matchups)})")
                    break
                picklist = list(available - disqual_part - disqual_opp)
                opp = random.choice(picklist)
                available.remove(opp)
                matchups.add((team, opp))
            if len(matchups) < self.nmatchups:
                matchups = set()
                continue
            break
        if len(matchups) < self.nmatchups:
            self.print_retries()
            match_idx = self.retry_match[rnd][-1]
            raise RuntimeError(f"Unable to pick matchups (round {rnd}, match idx {match_idx})")
        assert len(teams) % 2 == 0

        for matchup in matchups:
            (p1, p2), (p3, p4) = matchup
            self.opp_hist[p1][p3] += 1
            self.opp_hist[p1][p4] += 1
            self.opp_hist[p2][p3] += 1
            self.opp_hist[p2][p4] += 1
            self.opp_hist[p3][p1] += 1
            self.opp_hist[p3][p2] += 1
            self.opp_hist[p4][p1] += 1
            self.opp_hist[p4][p2] += 1
        self.rnd_matchups.append(matchups)
        return matchups

    def build(self) -> None:
        """Go through the processing of bulding the bracket (i.e. picking all of the
        matchups across rounds).
        """
        for rnd in range(self.nrounds):
            byes     = self.pick_byes(rnd)
            teams    = self.pick_teams(rnd, byes)
            matchups = self.pick_matchups(rnd, teams)

    def evaluate(self) -> None:
        """Evaluate the bracket in terms of aggregations on the ``PlayerData`` values.
        The resulting analysis is stored in ``self.stats``.
        """
        all_stats = {}
        for datum in PlayerData:
            all_stats[datum] = []

        for player in range(self.nplayers):
            pl_stats = {}
            for datum in PlayerData:
                pl_stats[datum] = 0

            pl_stats[PlayerData.DIST_PARTS] += len(self.part_hist[player])

            opp_list = self.opp_hist[player].copy()
            pl_stats[PlayerData.DIST_OPPS] = len(opp_list) - opp_list.count(0)

            int_list = opp_list.copy()
            for part in self.part_hist[player]:
                int_list[part] += 1
            pl_stats[PlayerData.DIST_INTS] = len(int_list) - int_list.count(0)

            # tabulate second level interactions
            l2_part = [0] * self.nplayers
            l2_opp  = [0] * self.nplayers
            l2_int  = [0] * self.nplayers
            for other in range(self.nplayers):
                if other == player:
                    continue
                # OPEN ISSUE: should we include L1 interactions in L2 tabulation???
                # tabulate partner path (doesn't touch l2_opp)
                if other in self.part_hist[player]:
                    for l2_other in range(self.nplayers):
                        if l2_other == player or l2_other == other:
                            continue
                        if l2_other in self.part_hist[other]:
                            l2_part[l2_other] += 1
                            l2_int[l2_other] += 1
                        l2_int[l2_other] += self.opp_hist[other][l2_other]
                # tabulate opponent path (doesn't touch l2_part)
                if self.opp_hist[player][other] > 0:
                    for l2_other in range(self.nplayers):
                        if l2_other == player or l2_other == other:
                            continue
                        if l2_other in self.part_hist[other]:
                            l2_int[l2_other] += 1
                        l2_opp[l2_other] += self.opp_hist[other][l2_other]
                        l2_int[l2_other] += self.opp_hist[other][l2_other]

            del l2_part[player]
            del l2_opp[player]
            del l2_int[player]

            pl_stats[PlayerData.DIST_PARTS_2] = len(l2_part) - l2_part.count(0)
            pl_stats[PlayerData.MEAN_PARTS_2] = round_val(mean(l2_part), 1)
            pl_stats[PlayerData.MIN_PARTS_2]  = min(l2_part)
            pl_stats[PlayerData.MAX_PARTS_2]  = max(l2_part)

            pl_stats[PlayerData.DIST_OPPS_2]  = len(l2_opp) - l2_opp.count(0)
            pl_stats[PlayerData.MEAN_OPPS_2]  = round_val(mean(l2_opp), 1)
            pl_stats[PlayerData.MIN_OPPS_2]   = min(l2_opp)
            pl_stats[PlayerData.MAX_OPPS_2]   = max(l2_opp)

            pl_stats[PlayerData.DIST_INTS_2]  = len(l2_int) - l2_int.count(0)
            pl_stats[PlayerData.MEAN_INTS_2]  = round_val(mean(l2_int), 1)
            pl_stats[PlayerData.MIN_INTS_2]   = min(l2_int)
            pl_stats[PlayerData.MAX_INTS_2]   = max(l2_int)

            for datum in PlayerData:
                all_stats[datum].append(pl_stats[datum])

        assert len(self.stats) == 0
        for datum in PlayerData:
            stats_agg = []
            for func in min, max, mean, stdev:
                stats_agg.append(func(all_stats[datum]))
            self.stats[datum] = stats_agg

    def print(self) -> None:
        """Print bye, team, and matchup information by round.
        """
        for rnd in range(self.nrounds):
            print(f"\nRound {rnd}:")
            print(f"  Byes: {self.rnd_byes[rnd]}")
            print("  Teams:")
            for idx, team in enumerate(self.rnd_teams[rnd]):
                print(f"    {idx:2d}: {team}")
            print("  Matchups:")
            for idx, matchup in enumerate(self.rnd_matchups[rnd]):
                print(f"    {idx:2d}: {matchup[0]} vs. {matchup[1]}")

        print(f"\n{'Stat':37}\tMin\tMax\tMean\tStddev")
        print(f"{'----':37}\t---\t---\t----\t------")
        for datum in PlayerData:
            stats_agg = self.stats[datum]
            print(f"{datum.value:32}\t{stats_agg[0]}\t{stats_agg[1]}\t{stats_agg[2]:.2f}\t" +
                  f"{stats_agg[3]:.2f}")

        self.print_retries()

    def print_retries(self) -> None:
        """Print some statistical information about retries when picking teams and
        matchups.  Higher numbers of retries are indicators of lower headroom in working
        within specified thresholds for repeated interactions, especially when the round
        number and/or team/match index is just below the maximum value.
        """
        print("\nTeam Retries:")
        for rnd, retries in enumerate(self.retry_team):
            if len(retries) == 0:
                continue
            print(f"Round {rnd}: {len(retries)} retries (mean idx {round_val(mean(retries))})")

        print("\nMatch Retries:")
        for rnd, retries in enumerate(self.retry_match):
            if len(retries) == 0:
                continue
            print(f"Round {rnd}: {len(retries)} retries (mean idx {round_val(mean(retries))})")

################
# command line #
################

def main() -> int:
    """Usage::

      $ python seed_round <nplayers>  <nrounds>

    To do:

    - Build multiple brackets and choose the one with the highest evaluation
    - Print a prettier/more structured version of the bracket
    - Develop a closed-form solution for optimality
    """
    nplayers = int(sys.argv[1])
    nrounds = int(sys.argv[2])

    bracket = Bracket(nplayers, nrounds)
    bracket.build()
    bracket.evaluate()
    bracket.print()

    return 0

if __name__ == "__main__":
    sys.exit(main())
