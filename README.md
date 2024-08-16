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
Statistic                           Min     Max     Mean    Stddev  Optimal
---------                           -----   -----   -----   ------  -------
Distinct Partners                   7       8       7.53    0.51    8
Distinct Opponents                  12      16      13.47   0.96    16
Distinct Interactions               19      24      21      1.33    24
Distinct 2nd-level Partners         25      31      28.24   1.52    33
Distinct 2nd-level Opponents        33      33      33      0.0     33
Distinct 2nd-level Interactions     33      33      33      0.0     33
2nd-level Partnerships (avg)        1.3     1.7     1.5     0.1     1.7
2nd-level Oppositions (avg)         5.1     6.8     5.71    0.4     6.79
2nd-level Interactions (avg)        12.4    15.7    13.75   0.82    15.27
2nd-level Partnerships Spread       3       4       3.59    0.5
2nd-level Oppositions Spread        5       10      7.76    1.39
2nd-level Interactions Spread       6       11      7.85    1.21

Divergence from Optimal             Min     Max     Mean
-----------------------             -----   -----   -----
Distinct Partners                   -1      0       -0.47
Distinct Opponents                  -4      0       -2.53
Distinct Interactions               -5      0       -3
Distinct 2nd-level Partners         -8      -2      -4.76
Distinct 2nd-level Opponents        0       0       0
Distinct 2nd-level Interactions     0       0       0
2nd-level Partnerships (avg)        -0.4    0.0     -0.19
2nd-level Oppositions (avg)         -1.69   0.01    -1.08
2nd-level Interactions (avg)        -2.87   0.43    -1.53
```

*Explanation of stats coming soon...*

## To Do

- Print a prettier/more structured version of the final bracket
- Develop a closed-form solution for optimality
