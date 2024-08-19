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
     0: (28, 33)
     1: (11, 7)
     2: (2, 17)
     3: (3, 27)
     4: (26, 14)
     5: (6, 5)
     6: (10, 24)
     7: (9, 22)
     8: (16, 19)
     9: (20, 4)
    10: (18, 32)
    11: (29, 12)
    12: (13, 25)
    13: (8, 21)
    14: (23, 30)
    15: (15, 31)
  Matchups:
     0: (13, 25) vs. (11, 7)
     1: (10, 24) vs. (23, 30)
     2: (16, 19) vs. (9, 22)
     3: (2, 17) vs. (29, 12)
     4: (15, 31) vs. (18, 32)
     5: (6, 5) vs. (26, 14)
     6: (20, 4) vs. (3, 27)
     7: (28, 33) vs. (8, 21)
```

## Statistics

Sample statistics output for the above bracket:

```
Statistic                          Min     Max     Mean    Stddev  Optimal
---------                          -----   -----   -----   ------  -------
Distinct Partners                  7       8       7.76    0.44    7.76
Distinct Opponents                 12      16      13.58   1.0     15.52
Distinct Interactions              20      24      21.33   1.19    23.27
Distinct 2nd-level Partners        25      31      27.94   1.48    32
Distinct 2nd-level Opponents       32      32      32      0.0     32
Distinct 2nd-level Interactions    32      32      32      0.0     32
2nd-level Partnerships (avg)       1.4     1.8     1.65    0.11    1.7
2nd-level Oppositions (avg)        5.2     7.3     6.1     0.47    6.79
2nd-level Interactions (avg)       13.7    16.9    14.82   0.85    15.27
2nd-level Partnerships Spread      3       5       3.88    0.6
2nd-level Oppositions Spread       6       11      8.52    1.54
2nd-level Interactions Spread      5       9       7.09    1.18

Divergence from Optimal            Min     Max     Mean
-----------------------            -----   -----   -----
Distinct Partners                  -0.76   0.24    0.0
Distinct Opponents                 -3.52   0.48    -1.94
Distinct Interactions              -3.27   0.73    -1.94
Distinct 2nd-level Partners        -7      -1      -4.06
Distinct 2nd-level Opponents       0       0       0
Distinct 2nd-level Interactions    0       0       0
2nd-level Partnerships (avg)       -0.3    0.1     -0.04
2nd-level Oppositions (avg)        -1.59   0.51    -0.69
2nd-level Interactions (avg)       -1.57   1.63    -0.45
```

*Explanation of stats coming soon...*

## To Do

- Print a prettier/more structured version of the final bracket
- Develop a closed-form solution for optimality
