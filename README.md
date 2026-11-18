# Kuku Promo Finder

**Assignment:** Kuku AI Generalist — Problem 1: Find the Promos  
**Show:** *I Married a Broken Soldier. He was a Duke* (50 episodes)

## What This Is

A tool that reads microdrama screenplay files and finds the best 20–60 second promo moments for Instagram, TikTok and YouTube. It uses a sliding-window scorer with keyword-based hook/cliffhanger detection — no API key required.

**Results:** 182 single-clip promos + 5 cross-episode montage promos found across 50 episodes, in ~3 seconds.

## Quick Start

```bash
# Install dependency
pip install streamlit

# Run analysis on all 50 episodes
python promo_finder.py

# Launch interactive app
streamlit run app.py
```

## Project Structure

```
kuku_assignment/
├── promo_finder.py          # Core analysis tool (run standalone)
├── app.py                   # Streamlit interactive app
├── requirements.txt
├── raw_outputs/
│   ├── all_promos.json      # Full output: 182 promos + 5 montages
│   └── top_promos.txt       # Human-readable top 10
└── scripts/
    └── I Married a Broken Soldier. He was a Duke/
        ├── episode-001-*.txt
        ├── episode-002-*.txt
        └── ... (50 episodes)
```

## Scoring Formula

```
total = hook_score × 2
      + emotional_score × 1.5
      + cliffhanger_score × 2
      + standalone_score × 1
```

| Dimension | What it measures | First/Last N seconds |
|---|---|---|
| Hook | Scroll-stopping action/line/camera | First 3s |
| Emotional | Intensity of dialogue + action | Whole window |
| Cliffhanger | Unresolved tension at cut | Last 5s |
| Standalone | Self-contained for cold audience | Whole window |

## Top 10 Promo Results

| # | Episode | Start → End | Duration | Score |
|---|---|---|---|---|
| 1 | 03 | 01:00 → 01:50 | 50s | 29.6 |
| 2 | 13 | 00:54 → 01:24 | 30s | 29.0 |
| 3 | 28 | 00:45 → 01:45 | 60s | 28.8 |
| 4 | 15 | 00:48 → 01:13 | 25s | 28.1 |
| 5 | 13 | 01:18 → 01:43 | 25s | 27.4 |
| 6 | 35 | 01:30 → 02:10 | 40s | 27.4 |
| 7 | 36 | 01:24 → 02:14 | 50s | 26.2 |
| 8 | 01 | 00:39 → 01:04 | 25s | 26.0 |
| 9 | 16 | 00:51 → 01:16 | 25s | 25.4 |
| 10 | 10 | 00:00 → 00:40 | 40s | 25.3 |

**Best cross-episode montage:** Ep9 (01:40→01:55) + Ep10 (00:00→00:15) — Score 32.1

## Limitations

- Cliffhanger detection misses visual tension (no keywords in script)
- Emotional score is diluted because ~60% of scripts are camera/action lines
- No visual quality assessment (lighting, shot composition)

## To run on a new show

```bash
python promo_finder.py --episode path/to/new_episode.txt
```

The script format must follow Kuku's standard: each beat has `**TYPE:**`, `Start: (MM:SS.ss) | End: (MM:SS.ss)`, and content on the next line.
