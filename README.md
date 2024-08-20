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
     0: (22, 15)
     1: (8, 4)
     2: (29, 7)
     3: (27, 30)
     4: (24, 20)
     5: (21, 3)
     6: (23, 13)
     7: (12, 19)
     8: (17, 9)
     9: (26, 10)
    10: (5, 32)
    11: (2, 6)
    12: (28, 25)
    13: (16, 14)
    14: (31, 18)
    15: (11, 33)
  Matchups:
     0: (2, 6) vs. (27, 30)
     1: (5, 32) vs. (11, 33)
     2: (8, 4) vs. (24, 20)
     3: (16, 14) vs. (17, 9)
     4: (21, 3) vs. (12, 19)
     5: (31, 18) vs. (26, 10)
     6: (29, 7) vs. (28, 25)
     7: (23, 13) vs. (22, 15)
```

## Statistics

Sample statistics output for the above bracket:

```
Statistic                               Min     Max     Mean    Stddev  Optimal
---------                               -----   -----   -----   ------  -------
Repeat Partners                         0       0       0       0.0
Repeat Opponents                        0       3       1.24    0.96
Repeat Interactions                     0       3       1.24    0.96
Distinct Partners                       7       8       7.53    0.51    7.53
Distinct Opponents                      12      16      13.82   1.11    15.06
Distinct Interactions                   19      24      21.35   1.47    22.59
2nd-level Partnerships (avg)            1.3     1.6     1.49    0.1     1.6
2nd-level Oppositions (avg)             5.0     6.8     5.86    0.5     6.39
2nd-level Interactions (avg)            12.1    15.8    13.99   0.97    14.37
2nd-level Partnerships Spread           3       5       3.79    0.64
2nd-level Oppositions Spread            5       10      7.18    1.42
2nd-level Interactions Spread           5       11      7.09    1.29

Divergence from Optimal                 Min     Max     Mean
-----------------------                 -----   -----   -----
Distinct Partners                       -0.53   0.47    0.0
Distinct Opponents                      -3.06   0.94    -1.24
Distinct Interactions                   -3.59   1.41    -1.24
2nd-level Partnerships (avg)            -0.3    0.0     -0.1
2nd-level Oppositions (avg)             -1.39   0.41    -0.52
2nd-level Interactions (avg)            -2.27   1.43    -0.39
```

*Explanation of stats coming soon...*

## To Do

- Print a prettier/more structured version of the final bracket
- Develop a closed-form solution for optimality
