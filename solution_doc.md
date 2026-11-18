# Kuku AI Generalist Assignment — Solution Document
### Problem 1: Find the Promos

**Show:** *I Married a Broken Soldier. He was a Duke*  
**Episodes analyzed:** 50  
**Total promo candidates found:** 182 (single-clip) + 5 cross-episode montages

---

## Problem Choice & Why

I chose **Problem 1** because it is the most directly impactful to Kuku's core business loop: getting new viewers to start watching a show. A promo finder that works on structured screenplay data can be automated end-to-end without an editor watching every episode, saving hours per show per week.

**Key assumption:** The best promos come from moments with a strong *visual/verbal hook* in the first 3 seconds AND either a natural cliffhanger ending or high emotional intensity across the clip. These criteria match how viral drama clips work on Instagram/TikTok (the first frame must stop a scroll; the last frame must create FOMO).

---

## How the Solution Works

### Input
A `.txt` episode script in Kuku's format: each beat tagged as `CAMERA`, `ACTION`, `DIALOGUE`, or `SOUND FX` with start/end timestamps.

### Algorithm: Sliding Window Scorer

```
For each episode:
  Parse all timestamped moments → list of beats
  Slide a 2-second-step window across [20s…60s] window sizes
  For each window:
    hook_score        = score first 3s (shocking actions/lines/camera)
    emotional_score   = avg emotional weight of all moments  
    cliffhanger_score = score last 5s (ominous SFX, cut-to-black, unanswered Q)
    standalone_score  = self-contained clarity (2+ speakers, no dangling refs)
    
    total = hook×2 + emotional×1.5 + cliffhanger×2 + standalone×1
    
  Deduplicate: keep best non-overlapping window per episode (max 5)

Cross-episode montage:
  Take Ep(N) last 15s + Ep(N+1) first 15s → score as single promo
```

### Key Scoring Keywords
| Dimension | Sample triggers |
|---|---|
| **Hook** | "slap", "grab", "gasp", "No!", "reveal", "violent", "extreme close-up", "What?!", "poison", "traitor" |
| **Emotional** | stage directions: *Devastated, Furious, Betrayed, Trembling, Horrified*; actions: *slaps, clenches, collapses* |
| **Cliffhanger** | "ominous swell", "cut to black", door slam, unanswered question, "this isn't over" |
| **Standalone** | 2+ named speakers, visible conflict, no dangling pronouns |

---

## Top Promo Recommendations

### Rank 1 — Best for TikTok/Instagram Launch
**Episode 3 | 01:00 → 01:50 (50s) | Score: 29.6**  
Hook: *Two royal guards burst in and forcibly drag Juliana backward*  
Cliffhanger: Scene ends as Juliana is hauled out — destination unknown  
Why it works: Instant visual action (guards grabbing a woman in a wedding gown = scroll-stopper). Zero context needed — the injustice reads immediately. The 50s fits a TikTok perfectly.

### Rank 2 — Best Cross-Episode Montage  
**Ep 9 (01:40→01:55) + Ep 10 (00:00→00:15) | 30s | Score: 32.1**  
Hook: *Nobleman snaps his head: "Where?"* → cut to Alexander bleeding in doorway  
Cliffhanger: Juliana gasps "Impossible." — a word with no answer  
Why it works: Classic episode-bridge promo. Abrupt cut mid-tension + first shot of blood creates extreme FOMO.

### Rank 3 — Best Viral Betrayal Moment
**Episode 1 | 00:39 → 01:04 (25s) | Score: 26.0**  
Hook: Clarissa smiles with cruel triumph: *"Because he is marrying me."*  
Cliffhanger: Juliana's tear + white-knuckled grip on her mother's gown  
Why it works: Highest standalone score (9/10). Anyone scrolling instantly understands: betrayal, sister, wedding.

### Rank 4 — Best Villain Reveal  
**Episode 16 | 00:51 → 01:16 (25s) | Score: 25.4**  
Hook: *Thug gasping, eyes wide*: "Harrington! Gerald Harrington paid us!"  
Why it works: One line of dialogue that reframes everything. High standalone — no context needed.

### Full Top 10 with Timestamps

| # | Ep | Start | End | Dur | Score | Post On |
|---|---|---|---|---|---|---|
| 1 | 03 | 01:00 | 01:50 | 50s | 29.6 | TikTok / IG |
| 2 | 13 | 00:54 | 01:24 | 30s | 29.0 | TikTok |
| 3 | 28 | 00:45 | 01:45 | 60s | 28.8 | YouTube |
| 4 | 15 | 00:48 | 01:13 | 25s | 28.1 | TikTok / IG |
| 5 | 13 | 01:18 | 01:43 | 25s | 27.4 | TikTok |
| 6 | 35 | 01:30 | 02:10 | 40s | 27.4 | IG Reels |
| 7 | 36 | 01:24 | 02:14 | 50s | 26.2 | IG / YouTube |
| 8 | 01 | 00:39 | 01:04 | 25s | 26.0 | TikTok / IG |
| 9 | 16 | 00:51 | 01:16 | 25s | 25.4 | TikTok |
| 10 | 10 | 00:00 | 00:40 | 40s | 25.3 | IG Reels |

**Cross-Episode Montages:**

| # | Episodes | Segments | Dur | Score | Opening Hook |
|---|---|---|---|---|---|
| M1 | Ep9→Ep10 | Ep9: 01:40–01:55 / Ep10: 00:00–00:15 | 30s | 32.1 | "Where?" → blood in doorway |
| M2 | Ep41→Ep42 | Ep41: 01:21–01:36 / Ep42: 00:00–00:15 | 30s | 28.9 | Cathedral explosion |
| M3 | Ep35→Ep36 | Ep35: 02:22–02:37 / Ep36: 00:00–00:15 | 30s | 28.0 | "Who?" + Alexander scar close-up |

### Posting Order Rationale
1. **Post Ep01 clip first** — the betrayal is the show's premise; zero prior context needed
2. **Post Ep03 clip second** — guards dragging her drives immediate outrage/curiosity
3. **Post Ep09→10 montage third** — episode-bridge cliff makes viewers binge
4. Rotate later-episode clips to pull mid-funnel viewers deeper (Ep13, 16)

---

## How It Scales

| Step | Current | At Kuku scale |
|---|---|---|
| Input | .txt script files | Same format — point at any new show folder |
| Speed | ~3s for 50 eps (pure Python) | Linear: 500 eps ≈ 30s |
| Human review | Optional spot-check | Editor reviews top 5 per show (saves ~80% of time vs. watching all) |
| Output | JSON + ranked text | Pipe to Notion / Sheets / CMS |

With a vision model API (GPT-4V, Gemini Vision): add a **visual quality layer** — score actual video frames for composition and face expressiveness, dimensions text alone can't see.

---

## Quality Check: Where the Tool Fails

**Cliffhanger detection is weak.** Most episode endings use SOUND FX cues the tool catches, but many real cliffhangers are built through *visual* tension (slow zoom on a face) with no keywords. Cliffhanger score is 0.0 for 7 of the top 10 promos — this is an undercount.

**Emotional intensity is diluted.** ~60% of each script is `CAMERA`/`ACTION` description (not dialogue), so emotional density scores are artificially low.

**What it gets right:** Hook detection is robust. Ep3, Ep13, Ep15, Ep28 all score 10/10 on hooks — spot-checking confirms these are genuinely scroll-stopping action moments.

---

## AI Tools Used

| Tool | Used for | Where it got it wrong |
|---|---|---|
| Claude Sonnet 4.5 (Antigravity) | PDF decoding, algorithm design, scoring logic, solution doc | Initially tried to decode PDF font glyphs byte-by-byte (produced garbage) — had to pivot to proper ToUnicode CMap extraction |
| Pure Python (no LLM API) | Script parsing, sliding window, all scoring | Keyword matching misses implicit emotion in visual descriptions |

**Key design decision:** Kept scoring fully algorithmic (no LLM per clip) so it runs on 50 episodes in 3 seconds at zero API cost. A lightweight LLM re-ranking pass on the top 20 candidates would be a natural upgrade.

---

*Assumptions: (1) "Best promos" = max hook + cliffhanger, not necessarily highest emotional intensity. (2) Single continuous clips preferred over montages for TikTok. (3) Standalone clarity matters for cold audiences (IG/TikTok) but less for YouTube where viewers follow the show.*
