#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Generate the matchups for the "seeding round" of a card-playing tournament (or any game
consisting of two-player teams competing head-to-head).  The seeding "round" (misnomer) is
actually a truncated round-robin tournament, with a predetermined number of rounds, in
which players switch partners for every round, and the players are ranked by best overall
individual performance.
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

Player  = int
Byes    = set[Player]
Team    = tuple[Player, Player]
Matchup = tuple[Team, Team]

class PlayerData(Enum):
    """Statistics for evaluating brackets
    """
    BYES         = "Byes"
    MATCHES      = "Matches"
    PARTS        = "Partners"
    OPPS         = "Opponents"
    DIST_OPPS    = "Distinct Opponents"
    INTS         = "Interactions"
    DIST_INTS    = "Distinct Interactions"
    DIST_PARTS_2 = "Distinct 2nd-level Partners"
    DIST_OPPS_2  = "Distinct 2nd-level Opponents"
    DIST_INTS_2  = "Distinct 2nd-level Interactions"

class Bracket:
    """Represents a possible bracket
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
    stats: dict[PlayerData, list[Number]]  # per stat, list contains [min, max, mean, stdev]

    def __init__(self, nplayers: int, nrounds: int):
        # this assumption is needed for logic in`pick_teams()`
        assert nplayers > nrounds
        
        self.nplayers  = nplayers
        self.nrounds   = nrounds
        self.nbyes     = self.nplayers % NPLAYERS
        self.nseats    = self.nplayers - self.nbyes
        self.nteams    = self.nseats // 2
        self.nmatchups = self.nteams // 2

        self.rnd_byes  = []
        self.rnd_teams = []
        self.rnd_matchups = []

        self.bye_hist  = set()
        self.part_hist = [set() for _ in range(self.nplayers)]
        self.opp_hist  = [[0] * self.nplayers for _ in range(self.nplayers)]

    def pick_byes(self, rnd: int) -> Byes:
        """Pick players that will get a bye this round; we just hardwire the selection to
        be sequential across rounds, to assure evenness
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
        the selection process if no qualified candidates remain
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
                    print(f"Retry picking teams (round {rnd}, team idx {len(teams)})")
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
            raise RuntimeError(f"Unable to pick teams (round {rnd}, team idx {len(teams)})")
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
        for maximum times an opposing player is seen
        """
        OPP_THRESH = 2
        matchups = set()
        for _ in range(50):
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
                    print(f"Retry picking matchup (round {rnd}, match idx {len(matchups)})")
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
            raise RuntimeError(f"Unable to pick matchups (round {rnd}, match idx {len(matchups)})")
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
        matchups across rounds)
        """
        for rnd in range(self.nrounds):
            byes     = self.pick_byes(rnd)
            teams    = self.pick_teams(rnd, byes)
            matchups = self.pick_matchups(rnd, teams)

    def evaluate(self) -> None:
        """Evaluate the bracket in terms of ``BracketStat`` values

        Stats for each player:
        - Byes
        - Matches
        - Partners
        - Opponents
        - Distinct opponents
        - Interactions
        - Distinct interactions
        - Distinct 2nd-level partners
        - Distinct 2nd-level opponents
        - Distinct 2nd-level interactions

        Summary report: min, max, mean, stdev for stats
        """
        all_stats = {
            PlayerData.BYES:         [],
            PlayerData.MATCHES:      [],
            PlayerData.PARTS:        [],
            PlayerData.OPPS:         [],
            PlayerData.DIST_OPPS:    [],
            PlayerData.INTS:         [],
            PlayerData.DIST_INTS:    [],
            PlayerData.DIST_PARTS_2: [],
            PlayerData.DIST_OPPS_2:  [],
            PlayerData.DIST_INTS_2:  []
        }

        for player in range(self.nplayers):
            pl_stats = {
                PlayerData.BYES:         0,
                PlayerData.MATCHES:      0,
                PlayerData.PARTS:        0,
                PlayerData.OPPS:         0,
                PlayerData.DIST_OPPS:    0,
                PlayerData.INTS:         0,
                PlayerData.DIST_INTS:    0,
                PlayerData.DIST_PARTS_2: 0,
                PlayerData.DIST_OPPS_2:  0,
                PlayerData.DIST_INTS_2:  0
            }
            
            if player in self.bye_hist:
                pl_stats[PlayerData.BYES] += 1
            # we can do this, since we guarantee no repeated partners
            pl_stats[PlayerData.MATCHES] += len(self.part_hist[player])
            pl_stats[PlayerData.PARTS] += len(self.part_hist[player])

            opp_list = self.opp_hist[player]
            pl_stats[PlayerData.OPPS] += sum(opp_list)
            pl_stats[PlayerData.DIST_OPPS] = len(opp_list) - opp_list.count(0)

            int_list = opp_list.copy()
            for part in self.part_hist[player]:
                int_list[part] += 1
            pl_stats[PlayerData.INTS] += sum(int_list)
            pl_stats[PlayerData.DIST_INTS] = len(int_list) - int_list.count(0)

            for datum in PlayerData:
                all_stats[datum].append(pl_stats[datum])

        stats = []
        print(f"{'Stat':32}\tMin\tMax\tMean\tStddev")
        for datum in PlayerData:
            stats_agg = []
            for func in min, max, mean, stdev:
                stats_agg.append(func(all_stats[datum]))
            print(f"{datum.value:32}\t{stats_agg[0]}\t{stats_agg[1]}\t{stats_agg[2]:.2f}\t" +
                  f"{stats_agg[3]:.2f}")

    def print(self) -> None:
        """Print bye, team, and matchup information by round
        """
        for rnd in range(self.nrounds):
            print(f"Round {rnd}:")
            for byes in self.rnd_byes[rnd]:
                print(f"  Byes: {byes}")
            print("  Teams:")
            for idx, team in enumerate(self.rnd_teams[rnd]):
                print(f"    {idx:2d}: {team}")
            print("  Matchups:")
            for idx, matchup in enumerate(self.rnd_matchups[rnd]):
                print(f"    {idx:2d}: {matchup[0]} vs. {matchup[1]}")

#####################
# command line tool #
#####################

def main() -> int:
    """Usage::

      $ python seed_round <nplayers>  <nrounds>
    """
    nplayers = int(sys.argv[1])
    nrounds = int(sys.argv[2])

    bracket = Bracket(nplayers, nrounds)
    bracket.build()
    bracket.print()
    bracket.evaluate()

    return 0

if __name__ == "__main__":
    sys.exit(main())
