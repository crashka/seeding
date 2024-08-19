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
     0: (20, 5)
     1: (30, 8)
     2: (25, 3)
     3: (21, 29)
     4: (32, 14)
     5: (2, 10)
     6: (27, 4)
     7: (18, 16)
     8: (15, 13)
     9: (17, 9)
    10: (28, 22)
    11: (23, 12)
    12: (6, 26)
    13: (31, 19)
    14: (33, 11)
    15: (7, 24)
  Matchups:
     0: (27, 4) vs. (21, 29)
     1: (30, 8) vs. (20, 5)
     2: (7, 24) vs. (23, 12)
     3: (33, 11) vs. (28, 22)
     4: (31, 19) vs. (17, 9)
     5: (25, 3) vs. (32, 14)
     6: (6, 26) vs. (2, 10)
     7: (18, 16) vs. (15, 13)
```

## Statistics

Sample statistics output for the above bracket:

```
Statistic                          Min     Max     Mean    Stddev  Optimal
---------                          -----   -----   -----   ------  -------
Distinct Partners                  7       8       7.53    0.51    7.53
Distinct Opponents                 12      16      13.65   1.25    15.06
Distinct Interactions              19      24      21.18   1.64    22.59
Distinct 2nd-level Partners        25      30      27.76   1.28    33
Distinct 2nd-level Opponents       33      33      33      0.0     33
Distinct 2nd-level Interactions    33      33      33      0.0     33
2nd-level Partnerships (avg)       1.3     1.6     1.49    0.1     1.6
2nd-level Oppositions (avg)        5.0     6.9     5.79    0.55    6.39
2nd-level Interactions (avg)       12.4    15.7    13.87   1.02    14.37
2nd-level Partnerships Spread      3       5       3.71    0.58
2nd-level Oppositions Spread       6       9       7.26    1.14
2nd-level Interactions Spread      5       9       6.94    1.07

Divergence from Optimal            Min     Max     Mean
-----------------------            -----   -----   -----
Distinct Partners                  -0.53   0.47    0.0
Distinct Opponents                 -3.06   0.94    -1.41
Distinct Interactions              -3.59   1.41    -1.41
Distinct 2nd-level Partners        -8      -3      -5.24
Distinct 2nd-level Opponents       0       0       0
Distinct 2nd-level Interactions    0       0       0
2nd-level Partnerships (avg)       -0.3    0.0     -0.11
2nd-level Oppositions (avg)        -1.39   0.51    -0.59
2nd-level Interactions (avg)       -1.97   1.33    -0.5
```

*Explanation of stats coming soon...*

## To Do

- Print a prettier/more structured version of the final bracket
- Develop a closed-form solution for optimality
