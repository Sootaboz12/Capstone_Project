# NFL entropy diagrams

Follows Figure 11 in [Google's exact binary splitter article](https://developers.google.com/machine-learning/decision-forests/binary-classification): frequency, positive-label ratio, entropy, and information gain.

- Data: [nflverse 2024 play-by-play](https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_2024.parquet), downloaded November 4, 2026. The figures use one training season, not the model's entire training dataset.
- Filters and possession-team win label match `next_play_model_testing.py`: run/pass/punt/field goal, known possession and non-tied final result, and nonmissing required situation fields.
- Each play is an observation; repeated plays from a game share its eventual outcome. These are descriptive play-level rates.
- F means feature < t; T means feature >= t; D means all eligible plays. Score differential is the possessing team's score minus its opponent's before the play.
- Our splitter sorts the feature and evaluates every midpoint between distinct values. Information gain uses group-size-weighted binary entropy in bits. Following the article, all nonempty splits are eligible; there is no minimum group-size restriction. Ties select the first maximum.
- Only the histogram uses bins. The splitter uses the exact distinct values. The lines connect evaluated thresholds.
- No model is imported, trained, or run. Existing source files, notebooks, and project dependencies are unchanged.

All three figures use the same 38,187 plays from 285 games. Their best splits are:

| Feature | Threshold | Win rate below | Win rate at/above | Information gain (bits) |
|---|---:|---:|---:|---:|
| Score differential | -3.5 points | 18.5% | 68.8% | 0.179851 |
| Yards to opponent's end zone | 42.5 yards | 54.7% | 47.5% | 0.003544 |
| Yards to go | 8.5 yards | 52.2% | 48.9% | 0.000776 |

Lower `yardline_100` means closer to the opponent's end zone. `ydstogo` is the distance needed for a first down or touchdown in a goal-to-go situation. Score differential has much stronger single-feature separation here. A low gain does not mean a feature is unhelpful when combined with other features.

The information-gain axes have different scales, so compare their numerical values rather than peak heights. Rare extreme situations can have pure outcomes but contribute little gain because they have few observations. These results are descriptive, not held-out validation.

Run these commands from the repository root using a Python environment with numpy, pandas, pyarrow, and matplotlib:

```sh
curl -L --fail -o /tmp/pbp-2024.parquet https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_2024.parquet
python src/model/experimental/entropy_diagrams/first_diagram.py --data /tmp/pbp-2024.parquet
python src/model/experimental/entropy_diagrams/first_diagram.py --data /tmp/pbp-2024.parquet --feature yardline_100
python src/model/experimental/entropy_diagrams/first_diagram.py --data /tmp/pbp-2024.parquet --feature ydstogo
python -m unittest discover -s src/model/experimental/entropy_diagrams -p 'test_*.py'
```

Files are grouped as follows:

```text
entropy_diagrams/
    first_diagram.py       Plotting script and exact entropy splitter
    test_first_diagram.py  Splitter tests
    README.md
    outputs/               Generated PNGs, SVGs, and threshold CSVs
```

View the figures: [score differential](outputs/score_differential.png), [field position](outputs/yardline_100.png), and [yards to go](outputs/ydstogo.png). Each has an editable SVG and a CSV of all candidate thresholds and statistics beside it. Use `--output` to choose a different output path stem.
