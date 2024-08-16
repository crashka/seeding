#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The objective here is to generate matchups for the "seeding round" of a card-playing
tournament (or any game consisting of two-player teams competing head-to-head).  The
seeding "round" (misnomer) is actually a truncated round-robin tournament in itself, with
a predetermined number of inner-rounds, in which players change partners for each round.
The players are then ranked by best overall individual performance.

This script implements a brute force approach, wherein we specify constraints and/or
thresholds for the number and type of interactions allowed between players across the
rounds, and generate random picks for byes, teams, and matchups for each round that
conform to the rules.  We then define evaluation functions that indicate the actual levels
of repeated interactions and/or diversity of experience (e.g. uniqueness in second-level
interactions).  We can thus generate a number of conforming brackets and choose the one
that demonstrates the best metrics (though it will almost certainly be suboptimal).
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
    DIST_INTS    = "Distinct Interactions"
    DIST_PARTS_2 = "Distinct 2nd-level Partners"
    DIST_OPPS_2  = "Distinct 2nd-level Opponents"
    DIST_INTS_2  = "Distinct 2nd-level Interactions"
    MEAN_PARTS_2 = "2nd-level Partnerships (avg)"
    MEAN_OPPS_2  = "2nd-level Oppositions (avg)"
    MEAN_INTS_2  = "2nd-level Interactions (avg)"
    SPRD_PARTS_2 = "2nd-level Partnerships Spread"
    SPRD_OPPS_2  = "2nd-level Oppositions Spread"
    SPRD_INTS_2  = "2nd-level Interactions Spread"

EvalStats = dict[PlayerData, list[Number]]  # list contains [min, max, mean, stdev opt]

FLOAT_PREC = 2

# opponent threshold progression for specified number of rounds (or multiples thereof)--
# otherwise, fall back to default proportional progression (represented by key `None`);
# this is definitely HACKY, hardwiring a custom config for the (currently) standard
# eight-round format (though also not otherwise unreasonable)!
OPP_THRESH = {
    8:    [1, 1, 1, 1, 1, 2, 2, 2],
    None: [1, 2]
}

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

    # other parameters
    opp_thresh:   list[int]       # max number of times an opponent can be seen

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
    stats:       EvalStats        # PlayerData aggregations (see type definition)
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

        if self.nrounds in OPP_THRESH:
            self.opp_thresh = OPP_THRESH[self.nrounds]
        else:
            self.opp_thresh = OPP_THRESH[None]
            # repeat final threshold as a backstop, if it might be needed
            if self.nrounds % len(self.opp_thresh) > 0:
                self.opp_thresh.append(self.opp_thresh[-1])
        assert self.opp_thresh and isinstance(self.opp_thresh, list)

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
        RETRIES = 10
        teams = set()
        all_players = range(self.nplayers)
        rnd_players = set(all_players) - byes
        assert len(rnd_players) == self.nseats
        # pick partners at random, given that we don't have some kind of smart rotational
        # algorithm for this; we outright exclude previous partners (since we don't have
        # to try and minimize partnerships, since we are asserting more players than
        # rounds) as well as previous opponents (though we may have to revisit this one,
        # if/when the numbers say we have to relax this, as in `pick_matchups()`)
        for _ in range(RETRIES):
            available = rnd_players.copy()
            while available:
                player = random.choice(list(available))
                available.remove(player)
                disqual_part = self.part_hist[player]
                disqual_opp = {other for other in available
                               if self.opp_hist[player][other] > 0}
                if available <= disqual_part | disqual_opp:
                    self.retry_team[rnd].append(len(teams))
                    break
                picklist = list(available - disqual_part - disqual_opp)
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
        RETRIES = 100
        # local parameters/thresholds
        thresh_allot = self.nrounds // len(self.opp_thresh)
        opp_thresh = self.opp_thresh[rnd // thresh_allot]

        matchups = set()
        for idx in range(RETRIES):
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
                        if (self.opp_hist[player][opp[0]] >= opp_thresh or
                            self.opp_hist[player][opp[1]] >= opp_thresh):
                            disqual_opp.add(opp)
                if available <= disqual_part | disqual_opp:
                    self.retry_match[rnd].append(len(matchups))
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
            pl_stats[PlayerData.SPRD_PARTS_2] = max(l2_part) - min(l2_part)

            pl_stats[PlayerData.DIST_OPPS_2]  = len(l2_opp) - l2_opp.count(0)
            pl_stats[PlayerData.MEAN_OPPS_2]  = round_val(mean(l2_opp), 1)
            pl_stats[PlayerData.SPRD_OPPS_2]  = max(l2_opp) - min(l2_opp)

            pl_stats[PlayerData.DIST_INTS_2]  = len(l2_int) - l2_int.count(0)
            pl_stats[PlayerData.MEAN_INTS_2]  = round_val(mean(l2_int), 1)
            pl_stats[PlayerData.SPRD_INTS_2]  = max(l2_int) - min(l2_int)

            for datum in PlayerData:
                all_stats[datum].append(pl_stats[datum])

        # level 1 interactions (total)
        npart        = self.nrounds
        nopp         = self.nrounds * 2
        nint         = self.nrounds * 3
        # level 2 interactions (total)
        npart_l2     = npart * (self.nrounds - 1)
        nopp_l2      = nopp  * (self.nrounds - 1) * 2
        nint_l2      = nint  * (self.nrounds - 1) * 3
        # level 2 interactions (per player, expected)
        exp_npart_l2 = npart_l2 / (self.nplayers - 1)
        exp_nopp_l2  = nopp_l2  / (self.nplayers - 1)
        exp_nint_l2  = nint_l2  / (self.nplayers - 1)

        opt = {}
        opt[PlayerData.DIST_PARTS]   = min(npart,    self.nplayers - 1)
        opt[PlayerData.DIST_OPPS]    = min(nopp,     self.nplayers - 1)
        opt[PlayerData.DIST_INTS]    = min(nint,     self.nplayers - 1)
        opt[PlayerData.DIST_PARTS_2] = min(npart_l2, self.nplayers - 1)
        opt[PlayerData.DIST_OPPS_2]  = min(nopp_l2,  self.nplayers - 1)
        opt[PlayerData.DIST_INTS_2]  = min(nint_l2,  self.nplayers - 1)
        opt[PlayerData.MEAN_PARTS_2] = exp_npart_l2
        opt[PlayerData.MEAN_OPPS_2]  = exp_nopp_l2
        opt[PlayerData.MEAN_INTS_2]  = exp_nint_l2

        assert len(self.stats) == 0
        for datum in PlayerData:
            stats_agg = []
            for func in min, max, mean, stdev:
                stats_agg.append(func(all_stats[datum]))
            stats_agg.append(opt.get(datum))
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

        print(f"\n{'Statistic':32}\tMin\tMax\tMean\tStddev\tOptimal")
        print(f"{'---------':32}\t-----\t-----\t-----\t------\t-------")
        for datum in self.stats:
            agg = (round_val(self.stats[datum][0]),
                   round_val(self.stats[datum][1]),
                   round_val(self.stats[datum][2]),
                   round_val(self.stats[datum][3]),
                   round_val(self.stats[datum][4]) or '')
            print(f"{datum.value:32}\t{agg[0]}\t{agg[1]}\t{agg[2]}\t{agg[3]}\t{agg[4]}")

        self.print_divergence()
        self.print_retries()

    def print_divergence(self) -> None:
        """Print divergence from optimal value for min, max, and mean stats (if
        applicable).
        """
        print(f"\n{'Divergence from Optimal':32}\tMin\tMax\tMean")
        print(f"{'-----------------------':32}\t-----\t-----\t-----")
        for datum, vals in self.stats.items():
            if vals[4] is None:
                continue
            div = (round_val(vals[0] - vals[4]),
                   round_val(vals[1] - vals[4]),
                   round_val(vals[2] - vals[4]))
            print(f"{datum.value:32}\t{div[0]}\t{div[1]}\t{div[2]}")

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

NTRIES = 20

def best_bracket(nplayers: int, nrounds: int, iters: int) -> Bracket:
    """Find the bracket with the best performing evaluation metrics.

    For now, the encoding of the selection criteria is hardwired, but later we can pass in
    options for it from the command line.
    """
    def cmp(b1: Bracket, b2: Bracket) -> int:
        """Return `True` if `b1` scores higher than `b2`, `False` if `b1` scores lower
        than `b2`.
        """
        if not b2:
            return True
        dist_int1 = b1.stats[PlayerData.DIST_INTS]
        dist_int2 = b2.stats[PlayerData.DIST_INTS]
        sprd_int1 = b1.stats[PlayerData.SPRD_INTS_2]
        sprd_int2 = b2.stats[PlayerData.SPRD_INTS_2]
        # criterion 1: highest minimum distinct interactions (direct)
        # criterion 2: highest mean distinct interactions (direct)
        # criterion 3: lowest mean level 2 interaction spread
        if dist_int1[0] != dist_int2[0]:
            return dist_int1[0] > dist_int2[0]
        else:
            if dist_int1[2] != dist_int2[2]:
                return dist_int1[2] > dist_int2[2]
            else:
                return sprd_int1[2] < sprd_int2[2]

    best = None
    failures = 0
    for _ in range(iters):
        bracket = build_bracket(nplayers, nrounds)
        if not bracket:
            failures += 1
            continue
        if cmp(bracket, best):
            best = bracket

    if failures:
        print(f"Failures: {failures}/{iters} searching for best bracket")
    return best

def build_bracket(nplayers: int, nrounds: int) -> Bracket:
    """Attempt to build a bracket with the specified parameters.  Return ``None`` if
    unable to (typically because the constraints are too tight).
    """
    for _ in range(NTRIES):
        bracket = Bracket(nplayers, nrounds)
        try:
            bracket.build()
        except RuntimeError as e:
            print(e)
            print("Rebuilding bracket...")
            continue
        bracket.evaluate()
        break

    if not bracket.stats:
        return None
    return bracket

def main() -> int:
    """Usage::

      $ python seed_round <nplayers> <nrounds> [<iterations>]

    where ``iterations`` indicates the number of iterations to use in searching for the
    best performing bracket; if ``iterations`` is not specified, the first bracket
    generated will be returned

    To do:

    - Print a prettier/more structured version of the final bracket
    - Develop a closed-form solution for optimality
    """
    best_iter = None
    nplayers  = int(sys.argv[1])
    nrounds   = int(sys.argv[2])
    if len(sys.argv) > 3:
        best_iter = int(sys.argv[3])

    if best_iter:
        bracket = best_bracket(nplayers, nrounds, best_iter)
        assert bracket
    else:
        bracket = build_bracket(nplayers, nrounds)
        if not bracket:
            print(f"Unable to build bracket after {NTRIES} attempts")
            return 1

    bracket.print()
    return 0

if __name__ == "__main__":
    sys.exit(main())
