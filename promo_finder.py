"""
Promo Finder Tool for "I Married a Broken Soldier. He was a Duke"
=================================================================
Reads microdrama screenplay files and finds the best 20-60 second promo moments.
Scores each moment based on hook strength, emotional intensity, cliffhanger potential,
and standalone clarity.

Usage:
    python promo_finder.py                        # Run on all 50 episodes
    python promo_finder.py --episode <path>       # Run on a single episode
    python promo_finder.py --top 10               # Show top N promos
"""

import re
import json
import os
import sys
import argparse
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Tuple
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants / keyword tables
# ---------------------------------------------------------------------------

HOOK_KEYWORDS = [
    "slap", "slaps", "slapped",
    "shock", "shocked", "shocking",
    "reveal", "revealed",
    "gasp", "gasps",
    "grab", "grabs", "grabbed",
    "no!", "what?", "how dare",
    "sudden", "suddenly",
    "burst", "bursts",
    "scream", "screams", "screaming",
    "cry out", "cries out",
    "collapse", "collapses",
    "strike", "strikes",
    "storm", "storms",
    "interrupt", "interrupts",
    "charge", "charges",
    "confronts", "confronted",
    "attacks", "attacked",
    "pulls out", "draws sword",
    "knife", "dagger", "weapon",
    "blood", "bleeding", "bloodied",
    "fire!", "help!", "stop!",
    "runs", "sprints", "bolts",
    "forbidden",
    "impossible",
    "betrayal", "betrayed",
]

HOOK_CAMERA_KEYWORDS = [
    "extreme close-up",
    "push-in",
    "smash cut",
    "whip pan",
    "crash zoom",
    "hard cut",
    "low-angle",
    "dramatic",
    "rapid",
]

EMOTIONAL_STAGE_DIRECTIONS = [
    "devastated", "furious", "shocked", "betrayed", "crying",
    "pleading", "desperate", "heartbroken", "weeping", "sobbing",
    "trembling", "shaking", "anguished", "outraged", "accusing",
    "horrified", "crushed", "gasping", "broken", "choking",
    "enraged", "bitter", "defiant", "fierce", "piercing",
    "alarmed", "terror", "tearful", "distraught", "tortured",
    "raw", "painful", "shattered", "disbelieving", "incredulous",
    "resolute", "steely", "cold fury", "quiet rage",
]

EMOTIONAL_ACTIONS = [
    "tears", "crying", "weep", "weeps", "wept",
    "sob", "sobs", "sobbing",
    "embrace", "embraces", "embraced",
    "collapse", "collapses", "collapsed",
    "confrontation", "confronts",
    "clutches", "clutching", "clenches",
    "kneel", "kneels", "knelt",
    "rage", "raging",
    "shakes", "trembles", "quivers",
    "spills over", "streams down",
    "white-knuckled", "knuckles whitening",
]

CLIFFHANGER_SOUND = [
    "ominous", "cliffhanger", "dramatic sting", "tense", "suspenseful",
    "swells", "mounting", "dread", "foreboding", "tension",
    "low drone", "dissonant", "unsettling",
]

CLIFFHANGER_ACTIONS = [
    "cut to black",
    "walks away without answering",
    "door slams", "slams the door", "door closing",
    "turns away", "turns his back", "turns her back",
    "silence falls", "falls silent",
    "storm out", "storms out",
    "unanswered",
    "fade to black",
    "freeze frame",
    "hard cut",
]

CLIFFHANGER_DIALOGUE = [
    "you will regret",
    "this is not over",
    "i will never forgive",
    "you don't know",
    "there is something you don't",
    "i have a secret",
    "i know who you",
    "everything will change",
    "wait until",
    "mark my words",
    "you have no idea",
    "who are you really",
    "what are you hiding",
    "it cannot be",
    "impossible",
    "then it's true",
    "i knew it",
    "you lied",
]

STANDALONE_POSITIVE = [
    "lady juliana", "juliana",
    "duke alexander", "alexander",
    "gerald", "clarissa",
    "father", "lord ashcroft",
    "sister",
    "wife", "husband",
    "wedding", "altar", "cathedral",
    "war", "soldier", "veteran", "duke",
    "scar", "scarred",
    "love", "marry", "marriage",
]

STANDALONE_NEGATIVE = [
    "as i was saying",
    "continuing from before",
    "as we discussed",
    "earlier i told you",
    "you remember when",
]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Moment:
    """A single timestamped beat (camera, action, dialogue, sound FX)."""
    moment_type: str          # CAMERA | ACTION | DIALOGUE | SOUND_FX
    speaker: Optional[str]    # for DIALOGUE
    stage_direction: str      # stage direction text (speaker emotion)
    text: str                 # content
    start: float              # seconds
    end: float                # seconds
    line_number: int

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class Scene:
    heading: str
    start: float
    end: float
    moments: List[Moment] = field(default_factory=list)

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class PromoWindow:
    episode_number: int
    episode_file: str
    start_time: float
    end_time: float
    duration: float
    moments: List[Moment]
    hook_score: float
    emotional_score: float
    cliffhanger_score: float
    standalone_score: float
    total_score: float
    hook_description: str
    cliffhanger_description: str
    reasoning: str

    def to_dict(self) -> dict:
        d = asdict(self)
        d['moments'] = [
            {
                'type': m['moment_type'],
                'speaker': m['speaker'],
                'stage_dir': m['stage_direction'],
                'text': m['text'][:120],
                'start': m['start'],
                'end': m['end'],
            }
            for m in d['moments']
        ]
        return d

    def format_time(self, t: float) -> str:
        m = int(t) // 60
        s = t - m * 60
        return f"{m:02d}:{s:05.2f}"

    def __str__(self):
        return (
            f"[Ep{self.episode_number:02d}] {self.format_time(self.start_time)} - "
            f"{self.format_time(self.end_time)} "
            f"(dur:{self.duration:.1f}s | score:{self.total_score:.2f})\n"
            f"  HOOK: {self.hook_description}\n"
            f"  CLIFFHANGER: {self.cliffhanger_description}\n"
            f"  WHY IT WORKS: {self.reasoning}"
        )


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

TIME_RE = re.compile(r'\((\d+):(\d+)\.(\d+)\)')


def parse_time(ts: str) -> float:
    """Convert MM:SS.cc string to float seconds."""
    m = TIME_RE.search(ts)
    if not m:
        return 0.0
    minutes = int(m.group(1))
    seconds = int(m.group(2))
    centiseconds = int(m.group(3))
    return minutes * 60 + seconds + centiseconds / 100.0


def parse_episode(filepath: str) -> Tuple[int, List[Scene]]:
    """Parse an episode file into a list of Scenes containing Moments."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Extract episode number from first line
    ep_num = 0
    for line in lines[:5]:
        m = re.search(r'Episode\s+(\d+)', line, re.IGNORECASE)
        if m:
            ep_num = int(m.group(1))
            break

    scenes: List[Scene] = []
    current_scene: Optional[Scene] = None
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        # Scene boundary
        if line.startswith('SCENE '):
            heading = ''
            scene_start = 0.0
            scene_end = 0.0
            j = i + 1
            while j < len(lines) and j < i + 6:
                l = lines[j].rstrip()
                if l.startswith('Scene heading:'):
                    heading = l.split(':', 1)[1].strip()
                elif l.startswith('Scene start:'):
                    scene_start = parse_time(l)
                elif l.startswith('Scene end:'):
                    scene_end = parse_time(l)
                j += 1
            current_scene = Scene(heading=heading, start=scene_start, end=scene_end)
            scenes.append(current_scene)
            i = j
            continue

        # Moment blocks: **TYPE:**  or **SPEAKER (direction):**
        bold_match = re.match(r'\*\*([^*]+)\*\*:?', line)
        if bold_match and current_scene is not None:
            header = bold_match.group(1).strip()

            # Determine type
            if header.upper() in ('CAMERA', 'ACTION', 'SOUND FX'):
                moment_type = header.upper().replace(' ', '_')
                speaker = None
                stage_direction = ''
            else:
                moment_type = 'DIALOGUE'
                sd_match = re.match(r'^(.+?)\s*\(([^)]*)\)\s*:?$', header)
                if sd_match:
                    speaker = sd_match.group(1).strip()
                    stage_direction = sd_match.group(2).strip()
                else:
                    speaker = header.rstrip(':')
                    stage_direction = ''

            # Read Start/End and content
            # Format: "Start: (MM:SS.cc) | End: (MM:SS.cc)" on a SINGLE line
            start_t = 0.0
            end_t = 0.0
            content_lines = []
            j = i + 1
            while j < len(lines):
                l = lines[j].rstrip()
                # Check for "Start: ... | End: ..." on one line
                if l.startswith('Start:') and '|' in l:
                    parts = l.split('|')
                    start_t = parse_time(parts[0])
                    if len(parts) > 1:
                        end_t = parse_time(parts[1])
                elif l.startswith('Start:'):
                    start_t = parse_time(l)
                elif l.startswith('End:'):
                    end_t = parse_time(l)
                elif re.match(r'\*\*[^*]+\*\*', l) or l.startswith('SCENE ') or l.startswith('--- SCRIPT END'):
                    break
                elif l and not l.startswith('Start:') and not l.startswith('End:'):
                    content_lines.append(l.strip('"').strip())
                j += 1

            content = ' '.join(cl for cl in content_lines if cl)
            if start_t == 0.0 and end_t == 0.0:
                i += 1
                continue

            moment = Moment(
                moment_type=moment_type,
                speaker=speaker,
                stage_direction=stage_direction,
                text=content,
                start=start_t,
                end=end_t,
                line_number=i,
            )
            current_scene.moments.append(moment)
            i = j
            continue

        i += 1

    return ep_num, scenes


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def _has_any(text: str, keywords: List[str]) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


def score_hook(moments: List[Moment], window_start: float) -> Tuple[float, str]:
    """Score the hook potential of the first ~3 seconds of a window."""
    hook_moments = [m for m in moments if m.start - window_start <= 3.0]
    if not hook_moments:
        hook_moments = moments[:2] if moments else []

    score = 0.0
    desc_parts = []

    for m in hook_moments:
        full_text = f"{m.stage_direction} {m.text}".lower()

        if m.moment_type == 'CAMERA':
            if _has_any(full_text, HOOK_CAMERA_KEYWORDS):
                score += 2.5
                desc_parts.append(f"dramatic camera ({m.text[:60]})")

        if m.moment_type == 'ACTION':
            if _has_any(full_text, HOOK_KEYWORDS):
                score += 3.0
                desc_parts.append(f"shock action ({m.text[:60]})")

        if m.moment_type == 'DIALOGUE':
            if _has_any(m.stage_direction.lower(), ['shocked', 'gasping', 'furious', 'horrified', 'alarmed']):
                score += 2.0
            if _has_any(full_text, HOOK_KEYWORDS):
                score += 2.5
            if m == moments[0]:
                score += 1.0
            desc_parts.append(f"\"{m.text[:70]}\"")

        if m.moment_type == 'SOUND_FX':
            if _has_any(full_text, ['bang', 'crash', 'shatter', 'thunder', 'sting']):
                score += 2.0

    score = min(score, 10.0)
    desc = '; '.join(desc_parts[:2]) if desc_parts else 'Scene opening'
    return score, desc


def score_emotional(moments: List[Moment]) -> float:
    """Score average emotional intensity across all moments."""
    if not moments:
        return 0.0

    scores = []
    for m in moments:
        s = 0.0
        full_text = f"{m.stage_direction} {m.text}".lower()
        if m.moment_type == 'DIALOGUE':
            if _has_any(m.stage_direction.lower(), EMOTIONAL_STAGE_DIRECTIONS):
                s += 4.0
            if _has_any(full_text, EMOTIONAL_ACTIONS):
                s += 2.0
        elif m.moment_type == 'ACTION':
            if _has_any(full_text, EMOTIONAL_ACTIONS):
                s += 3.0
            if _has_any(full_text, EMOTIONAL_STAGE_DIRECTIONS):
                s += 2.0
        elif m.moment_type == 'CAMERA':
            if _has_any(full_text, ['extreme close-up', 'tears', 'trembling', 'crying', 'weeping']):
                s += 2.0
        scores.append(min(s, 10.0))

    return sum(scores) / len(scores)


def score_cliffhanger(moments: List[Moment], window_end: float) -> Tuple[float, str]:
    """Score the cliffhanger potential of the last ~5 seconds of a window."""
    cliff_moments = [m for m in moments if window_end - m.end <= 5.0]
    if not cliff_moments:
        cliff_moments = moments[-2:] if moments else []

    score = 0.0
    desc_parts = []

    for m in cliff_moments:
        full_text = f"{m.stage_direction} {m.text}".lower()

        if m.moment_type == 'SOUND_FX':
            if _has_any(full_text, CLIFFHANGER_SOUND):
                score += 3.5
                desc_parts.append(f"ominous sound FX ({m.text[:60]})")

        if m.moment_type == 'ACTION':
            if _has_any(full_text, CLIFFHANGER_ACTIONS):
                score += 3.0
                desc_parts.append(f"unresolved action ({m.text[:60]})")
            if 'cut to black' in full_text or 'fade to black' in full_text:
                score += 4.0

        if m.moment_type == 'CAMERA':
            if _has_any(full_text, ['cut to black', 'fade to black', 'freeze frame']):
                score += 4.0
            if _has_any(full_text, ['push-in', 'extreme close-up']):
                score += 1.5

        if m.moment_type == 'DIALOGUE':
            if _has_any(full_text, CLIFFHANGER_DIALOGUE):
                score += 2.5
                desc_parts.append(f"\"{m.text[:70]}\"")
            if _has_any(m.stage_direction.lower(), ['cold', 'ominous', 'cryptic', 'sinister', 'warning']):
                score += 1.5

    score = min(score, 10.0)
    desc = '; '.join(desc_parts[:2]) if desc_parts else 'Unresolved scene end'
    return score, desc


def score_standalone(moments: List[Moment], episode_number: int) -> float:
    """Score how well the window stands alone without prior context."""
    all_text = ' '.join(f"{m.stage_direction} {m.text}" for m in moments).lower()

    score = 5.0

    named_chars = sum(1 for kw in STANDALONE_POSITIVE if kw in all_text)
    score += min(named_chars * 0.5, 3.0)

    if _has_any(all_text, STANDALONE_NEGATIVE):
        score -= 2.0

    action_moments = [m for m in moments if m.moment_type == 'ACTION']
    if len(action_moments) >= 2:
        score += 1.0

    if episode_number <= 3:
        score += 1.0

    return min(max(score, 0.0), 10.0)


# ---------------------------------------------------------------------------
# Window evaluation
# ---------------------------------------------------------------------------

MIN_DURATION = 20.0
MAX_DURATION = 60.0
STEP = 1.0


def all_moments_in_range(scenes: List[Scene], start: float, end: float) -> List[Moment]:
    """Return all moments whose midpoint falls in [start, end]."""
    result = []
    for scene in scenes:
        for m in scene.moments:
            mid = (m.start + m.end) / 2.0
            if start <= mid <= end:
                result.append(m)
    return result


def find_best_windows(
    ep_num: int,
    filepath: str,
    scenes: List[Scene],
    top_n: int = 5,
) -> List[PromoWindow]:
    """Slide a window over the episode and score every 20-60 second chunk."""
    if not scenes:
        return []

    all_moms: List[Moment] = []
    for sc in scenes:
        all_moms.extend(sc.moments)

    if not all_moms:
        return []

    ep_start = all_moms[0].start
    ep_end = all_moms[-1].end

    candidates: List[PromoWindow] = []

    for duration in [25.0, 30.0, 40.0, 50.0, 60.0]:
        t = ep_start
        while t + duration <= ep_end + STEP:
            w_start = t
            w_end = min(t + duration, ep_end)
            w_moments = all_moments_in_range(scenes, w_start, w_end)

            if len(w_moments) < 3:
                t += STEP * 5
                continue

            hook_sc, hook_desc = score_hook(w_moments, w_start)
            emo_sc = score_emotional(w_moments)
            cliff_sc, cliff_desc = score_cliffhanger(w_moments, w_end)
            standalone_sc = score_standalone(w_moments, ep_num)

            total = (
                hook_sc * 2.0
                + emo_sc * 1.5
                + cliff_sc * 2.0
                + standalone_sc * 1.0
            )

            reasoning = _build_reasoning(hook_sc, emo_sc, cliff_sc, standalone_sc, w_moments)

            candidates.append(PromoWindow(
                episode_number=ep_num,
                episode_file=os.path.basename(filepath),
                start_time=w_start,
                end_time=w_end,
                duration=w_end - w_start,
                moments=w_moments,
                hook_score=round(hook_sc, 2),
                emotional_score=round(emo_sc, 2),
                cliffhanger_score=round(cliff_sc, 2),
                standalone_score=round(standalone_sc, 2),
                total_score=round(total, 2),
                hook_description=hook_desc,
                cliffhanger_description=cliff_desc,
                reasoning=reasoning,
            ))

            t += STEP * 3

    candidates.sort(key=lambda x: -x.total_score)
    deduped = _deduplicate(candidates, overlap_threshold=10.0)

    return deduped[:top_n]


def _deduplicate(windows: List[PromoWindow], overlap_threshold: float) -> List[PromoWindow]:
    """Remove windows that substantially overlap with a higher-scoring one."""
    kept = []
    for w in windows:
        overlaps = False
        for k in kept:
            overlap_start = max(w.start_time, k.start_time)
            overlap_end = min(w.end_time, k.end_time)
            overlap = max(0.0, overlap_end - overlap_start)
            if overlap >= overlap_threshold:
                overlaps = True
                break
        if not overlaps:
            kept.append(w)
    return kept


def _build_reasoning(hook: float, emo: float, cliff: float, standalone: float,
                     moments: List[Moment]) -> str:
    parts = []
    if hook >= 6:
        parts.append("Strong visual/dialogue hook that stops a scroll")
    elif hook >= 3:
        parts.append("Decent opening hook")
    if emo >= 5:
        parts.append("high emotional intensity throughout")
    if cliff >= 6:
        parts.append("powerful cliffhanger ending that demands the viewer continue")
    elif cliff >= 3:
        parts.append("partial cliffhanger tension")
    if standalone >= 7:
        parts.append("self-contained conflict — works for viewers with no prior context")

    all_text = ' '.join(m.text for m in moments).lower()
    if 'slap' in all_text:
        parts.append("contains slap — high-impact TikTok/Reel moment")
    if 'cut to black' in all_text or 'fade to black' in all_text:
        parts.append("ends on a cinematic cut-to-black")
    if any(m.moment_type == 'DIALOGUE' and 'clarissa' in m.text.lower() for m in moments):
        parts.append("Clarissa's cruelty on display — instant hate-watch engagement")

    return '; '.join(parts) if parts else 'Solid promo window with mixed emotional beats'


# ---------------------------------------------------------------------------
# Cross-episode montage promos
# ---------------------------------------------------------------------------

def find_cross_episode_promos(
    all_episodes: List[Tuple[int, str, List[Scene]]],
    top_n: int = 3,
) -> List[dict]:
    """
    Build montage promo specs by joining episode endings + next episode openings.
    """
    montages = []
    ep_map = {ep_num: (fp, scenes) for ep_num, fp, scenes in all_episodes}

    for ep_num, fp, scenes in all_episodes:
        if ep_num + 1 not in ep_map:
            continue

        all_moms = []
        for sc in scenes:
            all_moms.extend(sc.moments)
        if not all_moms:
            continue
        ep_end = all_moms[-1].end
        ending_moms = [m for m in all_moms if m.start >= ep_end - 15.0]

        next_fp, next_scenes = ep_map[ep_num + 1]
        next_moms_all = []
        for sc in next_scenes:
            next_moms_all.extend(sc.moments)
        if not next_moms_all:
            continue
        next_start = next_moms_all[0].start
        opening_moms = [m for m in next_moms_all if m.end <= next_start + 15.0]

        combined = ending_moms + opening_moms
        if len(combined) < 4:
            continue

        hook_sc, hook_desc = score_hook(combined, combined[0].start if combined else 0)
        emo_sc = score_emotional(combined)
        cliff_sc, cliff_desc = score_cliffhanger(combined, combined[-1].end if combined else 30)
        standalone_sc = score_standalone(combined, ep_num)

        total = hook_sc * 2.0 + emo_sc * 1.5 + cliff_sc * 2.0 + standalone_sc * 1.0

        montages.append({
            'type': 'cross_episode_montage',
            'episodes': [ep_num, ep_num + 1],
            'segment_1': {
                'episode': ep_num,
                'file': os.path.basename(fp),
                'start': round(ep_end - 15.0, 2),
                'end': round(ep_end, 2),
            },
            'segment_2': {
                'episode': ep_num + 1,
                'file': os.path.basename(next_fp),
                'start': round(next_start, 2),
                'end': round(next_start + 15.0, 2),
            },
            'total_duration': 30.0,
            'hook_score': round(hook_sc, 2),
            'emotional_score': round(emo_sc, 2),
            'cliffhanger_score': round(cliff_sc, 2),
            'standalone_score': round(standalone_sc, 2),
            'total_score': round(total, 2),
            'hook_description': hook_desc,
            'cliffhanger_description': cliff_desc,
        })

    montages.sort(key=lambda x: -x['total_score'])
    return montages[:top_n]


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_on_all_episodes(scripts_dir: str, output_dir: str, top_per_episode: int = 5):
    """Process all episode files and save output."""
    scripts_path = Path(scripts_dir)
    episode_files = sorted(scripts_path.glob('episode-*.txt'))

    if not episode_files:
        print(f"No episode files found in {scripts_dir}")
        return

    all_episodes = []
    all_promos: List[PromoWindow] = []

    print(f"Processing {len(episode_files)} episodes...")

    for ep_file in episode_files:
        print(f"  -> {ep_file.name}", end='', flush=True)
        try:
            ep_num, scenes = parse_episode(str(ep_file))
            all_episodes.append((ep_num, str(ep_file), scenes))
            windows = find_best_windows(ep_num, str(ep_file), scenes, top_n=top_per_episode)
            all_promos.extend(windows)
            print(f" [Ep{ep_num:02d}: {len(windows)} promos found]")
        except Exception as e:
            print(f" [ERROR: {e}]")

    print("Computing cross-episode montage promos...")
    montages = find_cross_episode_promos(all_episodes, top_n=5)

    all_promos.sort(key=lambda x: -x.total_score)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    json_data = {
        'show': 'I Married a Broken Soldier. He was a Duke',
        'total_episodes_processed': len(episode_files),
        'total_promos_found': len(all_promos),
        'single_clip_promos': [p.to_dict() for p in all_promos],
        'cross_episode_montages': montages,
    }

    json_file = output_path / 'all_promos.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)
    print(f"\nSaved full JSON -> {json_file}")

    top10_file = output_path / 'top_promos.txt'
    with open(top10_file, 'w', encoding='utf-8') as f:
        f.write('=' * 70 + '\n')
        f.write('TOP 10 PROMO RECOMMENDATIONS\n')
        f.write('Show: I Married a Broken Soldier. He was a Duke\n')
        f.write('=' * 70 + '\n\n')

        for rank, promo in enumerate(all_promos[:10], 1):
            f.write(f"#{rank} {promo}\n")
            f.write(f"  Scores -> Hook:{promo.hook_score} | Emotion:{promo.emotional_score:.2f} "
                    f"| Cliff:{promo.cliffhanger_score} | Standalone:{promo.standalone_score} "
                    f"| TOTAL:{promo.total_score}\n\n")

        if montages:
            f.write('\n' + '=' * 70 + '\n')
            f.write('TOP CROSS-EPISODE MONTAGE PROMOS\n')
            f.write('=' * 70 + '\n\n')
            for rank, m in enumerate(montages[:3], 1):
                f.write(f"#{rank} Montage: Episodes {m['episodes'][0]} -> {m['episodes'][1]} "
                        f"(~{m['total_duration']}s | score:{m['total_score']})\n")
                f.write(f"  Segment 1: Ep{m['episodes'][0]} "
                        f"{_fmt(m['segment_1']['start'])} - {_fmt(m['segment_1']['end'])}\n")
                f.write(f"  Segment 2: Ep{m['episodes'][1]} "
                        f"{_fmt(m['segment_2']['start'])} - {_fmt(m['segment_2']['end'])}\n")
                f.write(f"  HOOK: {m['hook_description']}\n")
                f.write(f"  CLIFFHANGER: {m['cliffhanger_description']}\n\n")

    print(f"Saved top promos -> {top10_file}")
    return all_promos, montages


def _fmt(t: float) -> str:
    m = int(t) // 60
    s = t - m * 60
    return f"{m:02d}:{s:05.2f}"


def run_on_single_episode(filepath: str, top_n: int = 5) -> List[PromoWindow]:
    """Process a single episode and return promo windows."""
    ep_num, scenes = parse_episode(filepath)
    windows = find_best_windows(ep_num, filepath, scenes, top_n=top_n)
    return windows


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Promo Finder for microdrama scripts')
    parser.add_argument('--scripts-dir', default=
        r'C:\Users\Monish\.gemini\antigravity\scratch\kuku_assignment\scripts'
        r'\I Married a Broken Soldier. He was a Duke',
        help='Directory containing episode .txt files')
    parser.add_argument('--output-dir', default=
        r'C:\Users\Monish\.gemini\antigravity\scratch\kuku_assignment\raw_outputs',
        help='Directory to write output files')
    parser.add_argument('--episode', default=None,
        help='Path to a single episode file (overrides --scripts-dir)')
    parser.add_argument('--top', type=int, default=5,
        help='Number of top promos to return per episode')
    args = parser.parse_args()

    if args.episode:
        promos = run_on_single_episode(args.episode, top_n=args.top)
        for rank, p in enumerate(promos, 1):
            print(f"\n#{rank} {p}")
            print(f"  Scores -> Hook:{p.hook_score} | Emotion:{p.emotional_score:.2f} "
                  f"| Cliff:{p.cliffhanger_score} | Standalone:{p.standalone_score} "
                  f"| TOTAL:{p.total_score}")
    else:
        run_on_all_episodes(args.scripts_dir, args.output_dir, top_per_episode=args.top)
