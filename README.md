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
     0: (31, 11)
     1: (6, 18)
     2: (7, 33)
     3: (25, 19)
     4: (26, 30)
     5: (27, 24)
     6: (5, 14)
     7: (13, 20)
     8: (29, 3)
     9: (21, 15)
    10: (23, 12)
    11: (28, 2)
    12: (32, 10)
    13: (17, 8)
    14: (22, 9)
    15: (16, 4)
  Matchups:
     0: (16, 4) vs. (17, 8)
     1: (22, 9) vs. (29, 3)
     2: (25, 19) vs. (27, 24)
     3: (26, 30) vs. (28, 2)
     4: (32, 10) vs. (31, 11)
     5: (6, 18) vs. (23, 12)
     6: (5, 14) vs. (13, 20)
     7: (21, 15) vs. (7, 33)
```

## Statistics

Here is the statistics output for the run that generated the example bracket above:

```
Statistic                               Min     Max     Mean    Stddev  Optimal
---------                               -----   -----   -----   ------  -------
Repeat Partners                         0       0       0       0.0
Repeat Opponents                        0       3       1.24    0.99
Repeat Interactions                     0       3       1.24    0.99
Distinct Partners                       7       8       7.53    0.51    7.53
Distinct Opponents                      12      16      13.82   1.03    15.06
Distinct Interactions                   19      24      21.35   1.37    22.59
2nd-level Partnerships (avg)            1.4     1.6     1.49    0.09    1.49
2nd-level Oppositions (avg)             5.0     6.9     5.87    0.44    6.42
2nd-level Interactions (avg)            12.5    15.8    13.98   0.85    14.78
2nd-level Partnerships Spread           3       4       3.38    0.49
2nd-level Oppositions Spread            6       11      8.09    1.24
2nd-level Interactions Spread           5       10      7.32    1.09

Divergence from Optimal                 Min     Max     Mean
-----------------------                 -----   -----   -----
Distinct Partners                       -0.53   0.47    0.0
Distinct Opponents                      -3.06   0.94    -1.24
Distinct Interactions                   -3.59   1.41    -1.24
2nd-level Partnerships (avg)            -0.09   0.11    0.0
2nd-level Oppositions (avg)             -1.42   0.48    -0.54
2nd-level Interactions (avg)            -2.28   1.02    -0.8
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
the sample run above shows an average of 1.24 repeat interactions (for any one player)
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
