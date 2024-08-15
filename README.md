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
$ python seed_round.py <nplayers>  <nrounds>
```

## To Do

- Build multiple brackets and choose the one with the highest evaluation
- Print a prettier/more structured version of the final bracket
- Develop a closed-form solution for optimality
