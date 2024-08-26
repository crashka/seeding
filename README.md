# Seed Round

The objective here is to generate matchups for the "seeding round" of a card-playing
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

## Usage

Command line interface:

```bash
$ python -m seed_round <nplayers> <nrounds> [<iterations>]
```

where `iterations` indicates the number of iterations to use in searching for the best
performing bracket; if `iterations` is not specified, the first bracket generated will be
returned.

## Brackets

A generated bracket (for `nplayers = 34` and `nrounds = 8`, in this case) currently looks
like this (only the first round shown):

```
Round 0:
  Byes: {0, 1}
  Teams:
     0: (13, 30)
     1: (16, 7)
     2: (23, 17)
     3: (29, 33)
     4: (15, 24)
     5: (28, 20)
     6: (31, 27)
     7: (18, 10)
     8: (11, 3)
     9: (25, 2)
    10: (22, 4)
    11: (12, 19)
    12: (26, 32)
    13: (21, 5)
    14: (8, 6)
    15: (9, 14)
  Matchups:
     0: (23, 17) vs. (18, 10)
     1: (11, 3) vs. (15, 24)
     2: (28, 20) vs. (26, 32)
     3: (31, 27) vs. (29, 33)
     4: (12, 19) vs. (21, 5)
     5: (22, 4) vs. (25, 2)
     6: (8, 6) vs. (9, 14)
     7: (16, 7) vs. (13, 30)
```

## Statistics

Here is the statistics output for the run that generated the example bracket above:

```
Statistic                               Min     Max     Mean    Stddev  Optimal
---------                               -----   -----   -----   ------  -------
Repeat Partners                         0       0       0       0.0
Repeat Opponents                        0       3       1.18    0.87
Repeat Interactions                     0       3       1.18    0.87
Distinct Partners                       7       8       7.53    0.51    7.53
Distinct Opponents                      12      16      13.88   1.39    15.06
Distinct Interactions                   19      24      21.41   1.81    22.59
2nd-level Partnerships (avg)            1.4     1.6     1.5     0.09    1.49
2nd-level Oppositions (avg)             4.9     6.9     5.92    0.61    6.42
2nd-level Interactions (avg)            12.2    15.9    14.05   1.2     14.78
2nd-level Partnerships Spread           3       6       3.74    0.9
2nd-level Oppositions Spread            5       9       7       0.98
2nd-level Interactions Spread           6       9       7.65    0.95

Divergence from Optimal                 Min     Max     Mean
-----------------------                 -----   -----   -----
Distinct Partners                       -0.53   0.47    0.0
Distinct Opponents                      -3.06   0.94    -1.18
Distinct Interactions                   -3.59   1.41    -1.18
2nd-level Partnerships (avg)            -0.09   0.11    0.01
2nd-level Oppositions (avg)             -1.52   0.48    -0.5
2nd-level Interactions (avg)            -2.58   1.12    -0.73
```

See next section for (partial) explanation of stats.

## What is Optimal?

So, let's talk through this using numbers from the above data for 34 players and 8 rounds:

- 34 players means 8 tables of 4 players per round, with 2 players gettng byes
- 8 rounds means a total of 16 byes, so players will have at most 1 bye for the entire
  sequence (with 18 players playing all 8 rounds)
- Every round, players who play will have 1 partner and 2 opponents, or 3 "interactions"
- Thus, across 8 rounds, players will have a maximum of 8 partners, 16 opponents, and 24
  interactions (7, 14, and 21, respectively, for those with a bye)
- Since there are more players than the max number of per-player interactions, assuming
  the objective is to have as many different interactions as possible, optimally there
  will be no repeat interactions between players

Ray solved this (i.e. no repeat interactions) for 32 and 33 players across 8 rounds (see
the `.csv` and `.stats` files in this repo), so it should also be solvable for 34 players
and above, since it only gets easier to avoid repeats as you add players.  The stats for
the sample run above shows an average of 1.18 repeat interactions (for any one player)
across the 8 rounds.  Suboptimal (should be zero).  Note that all of the repeats are
*repeat opponents*—this is because the script has a hardwired constraint of considering
only first time interactions when selecting partners.

Side notes:

- The optimal number of distinct interactions above is shown as 22.59 (instead of 24)
  because of the 16 byes (do the math)
- The stats for "2nd-level interactions" above refers to partners of partners, partners of
  opponents, and opponents of opponents.  For example, if a player has on average 22.59
  interactions with other players, and each of those interactees has `22.59 − 1 = 21.59`
  *other* interactions of their own, then there are a total of `22.59 × 21.59 = 487.64`
  2nd-level interactions.  If those interactions are perfectly distributed across the
  other 33 players, then there will be an average of `487.64 ÷ 33 = 14.78` 2nd-level
  interactions between any two players.

## To Do

- Print a prettier/more structured version of the final bracket
- Develop a closed-form solution for optimality
