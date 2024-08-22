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
     0: (8, 24)
     1: (12, 27)
     2: (29, 4)
     3: (2, 17)
     4: (18, 7)
     5: (25, 3)
     6: (32, 14)
     7: (28, 16)
     8: (11, 9)
     9: (23, 19)
    10: (20, 26)
    11: (33, 22)
    12: (6, 13)
    13: (5, 10)
    14: (30, 15)
    15: (31, 21)
  Matchups:
     0: (33, 22) vs. (18, 7)
     1: (23, 19) vs. (2, 17)
     2: (6, 13) vs. (31, 21)
     3: (30, 15) vs. (11, 9)
     4: (28, 16) vs. (5, 10)
     5: (25, 3) vs. (32, 14)
     6: (29, 4) vs. (20, 26)
     7: (12, 27) vs. (8, 24)
```

## Statistics

Here is the statistics output for the run that generated the example bracket above:

```
Statistic                               Min     Max     Mean    Stddev  Optimal
---------                               -----   -----   -----   ------  -------
Repeat Partners                         0       0       0       0.0
Repeat Opponents                        0       3       1.47    0.99
Repeat Interactions                     0       3       1.47    0.99
Distinct Partners                       7       8       7.53    0.51    7.53
Distinct Opponents                      12      16      13.59   1.1     15.06
Distinct Interactions                   19      24      21.12   1.45    22.59
2nd-level Partnerships (avg)            1.3     1.7     1.49    0.1     1.49
2nd-level Oppositions (avg)             5.0     6.8     5.76    0.47    6.42
2nd-level Interactions (avg)            12.3    15.8    13.83   0.9     14.78
2nd-level Partnerships Spread           3       5       3.74    0.57
2nd-level Oppositions Spread            5       10      7.5     1.42
2nd-level Interactions Spread           5       11      7.38    1.23

Divergence from Optimal                 Min     Max     Mean
-----------------------                 -----   -----   -----
Distinct Partners                       -0.53   0.47    0.0
Distinct Opponents                      -3.06   0.94    -1.47
Distinct Interactions                   -3.59   1.41    -1.47
2nd-level Partnerships (avg)            -0.19   0.21    0.0
2nd-level Oppositions (avg)             -1.42   0.38    -0.65
2nd-level Interactions (avg)            -2.48   1.02    -0.95
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
the CSV files in this repo), so it should also be solvable for 34 players and above, since
it only gets easier to avoid repeats as you add players.  The stats for the sample run
above shows an average of 1.47 repeat interactions (for any one player) across the 8
rounds.  Suboptimal.  Note that all of the repeats are repeat *opponents*, since the
script has a hardwired constraint of considering only first time interactions when
selecting partners.

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
