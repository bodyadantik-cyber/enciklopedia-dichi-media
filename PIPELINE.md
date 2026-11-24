# «Энциклопедия дичи» — daily video pipeline

Channel: TikTok `@enciklopedia.dichi`, YouTube «энциклопедии дичи» (UCgmhWB3uri4npe9zoDaFM-w).
Language: Russian. Format: vertical 1080×1920, 30 fps, **30–40 s** (since 23.11.2026: shorter = better completion on a new account), documentary-thriller tone.
Owner: Kyiv time (Europe/Kiev). Publishing goes through Metricool brand `8195352`.

**Time:** the container clock is UTC even if `TZ=Europe/Kiev date` prints "Europe". Get Kyiv time with
`python3 -c "from zoneinfo import ZoneInfo;from datetime import datetime;print(datetime.now(ZoneInfo('Europe/Kyiv')))"`.

## 1. Topic
- Read `topics.md` — never repeat a used topic. **Take the next item from the Backlog first**.
- **Series (Часть 1 / Часть 2 / …): make ALL parts in the same run and publish them the SAME DAY at different
  times**: Part 1 at 18:00, Part 2 at 21:00 (a third part goes to 18:00 of the next day).
  If the run is too late for that, the parts go to 18:00 / 21:00 of the next day. Each part is its own video, spec, commit and Metricool post.
  Part 1's end card and caption name the time of Part 2 (e.g. «ЧАСТЬ 2 — СЕГОДНЯ В 21:00»).
  If a series Part 1 was already published earlier and Part 2 is still missing, make Part 2 first. Only when the backlog is empty, find new topics as below
  and refill the backlog with 5–10 ideas.
- Look at what works: vidIQ (`vidiq_instagram_tiktok_outlier_search`, `vidiq_trending_videos`, `vidiq_outliers`)
  for facts / history / science / space / mysteries in Russian and English. Windsor (`tiktok_organic`, `youtube`)
  for our own last videos' views — lean toward what performed best.
- Pick ONE surprising, verifiable fact with a strong visual story (disasters, record-breaking things, strange history,
  space, deep sea, animals, human body, lost civilisations). No politics, no medical advice, no real private people,
  no copyrighted characters.

## 2. Script (≈70–90 Russian words → ~30–38 s of speech)
- Hook in the first sentence (shock number / paradox / "this happened for real"), max ~8 words.
- **The same hook is on screen as big text from frame 0** (a `labels` entry 0.0–~2.5 s, size 60–64, red) —
  most viewers scroll with sound off.
- 5–7 short sentences, concrete numbers, one comparison the viewer can feel.
- **Loop ending**: the last line should flow back into the first line (e.g. ends on a question the hook answers),
  so a rewatch feels seamless. No long outro — end card ≤1.5 s.
- Every number must be checked with WebSearch against ≥2 independent sources. Then spawn a separate
  fact-check agent (Agent tool, general-purpose) given ONLY the script, asking it to verify each claim with sources
  and list anything wrong. Fix everything it flags before generating audio.
- Numbers in the TTS text are written out as words; ElevenLabs eleven_v4 tags like [low, ominous], [tense],
  [whispering] are allowed.

## 3. Voice
- ElevenLabs `creative_generate_speech`, model `eleven_v4`, voice `ogi2DyUAKJb7CEdqqvlU` (Stanislav, deep RU),
  `generations_count: 1`.

## 4. Visuals (6–8 images) — CARTOON STYLE by default (since 24.11.2026, owner's choice)
- **Style:** 2D cartoon, modern animated-explainer look — flat colours with soft cel shading, bold dark outlines,
  subtle warm glow outline around the main character, expressive characters (simple round faces, big round white eyes,
  clear emotions and gestures). Start EVERY image prompt with:
  "Vertical 2D cartoon illustration, modern animated explainer style: flat colors with soft cel shading, bold dark outlines, a subtle warm glow outline around the main character."
- **Characters:** each story gets its own cast. Before prompting, write a fixed one-line look for every character
  (face, hair/beard, clothes, colours — e.g. "black bushy beard, brown cap, white linen peasant shirt with a red belt")
  and repeat it word for word in every image where they appear, so they stay recognisable. Show them DOING the beat
  (gesture, emotion), not posing. Real historical people: generic cartoon look, no attempt at a likeness.
  Never copy a known cartoon character or another channel's mascot.
- **Movement (characters move and gesture):** animate the 2–8 key frames with image-to-video and put the clips into the spec
  as `videos` (see `tools/render.py`: `"videos": {"v1": {"file": "clip.mp4", "speed": 1.0}}`, scene image key `"v1"`,
  Ken Burns zoom ~1.0→1.06 on video scenes). Tools, in order: Figma Weave `weave_run_model` with Seedance 2.0 Mini
  (id `c11c3ef1-32d2-48b4-83e9-0cc2a5599646`, 5 s, 720p, 9:16, generate_audio false, ~65 Weave credits/clip; prompt =
  "2D cartoon animation, keep the exact art style and character. <action>"), or ElevenLabs video models if credits allow.
  Download the result with curl. Priority: the hook scene and the scenes with people. **If no video credits are left
  (Weave free runs were used up on 24.11.2026), do not stop:** render the cartoon stills with the normal Ken Burns motion
  and say in the report that animation needs Weave/ElevenLabs credits.
- 005 (Tunguska) is the reference example of this style.
- ElevenLabs (full connector, the one that has `creative_generate_image`): `creative_create_flow`, then for each image
  `creative_add_flow_node` (node_type `image-generation`, model `gpt-image-2.5-sunburst`) →
  `creative_update_node` with `model_parameters: {"aspect_ratio": "9:16", "resolution": "1K", "quality": "high"}` and the prompt →
  `creative_run_flow_nodes` with `generations_count: 1` (all image nodes in one call). Do NOT use
  `creative_generate_image` directly: it starts at 16:9 before you can set the aspect.
- One image per beat of the story, always end with "No text."
- Fallback if ElevenLabs credits / the free daily image limit run out: Figma `generate_image` (model gpt-image-2.5-sunburst)
  into file `jMJ8vZ7sttWibAXAnajdlD`, 1024×1820 — the returned `image.url` downloads fine with `curl -f -L` (checked 23.11.2026).

## 5. Getting files into the workspace
- ElevenLabs images and voice: `creative_get_flow_run_status` → each generation's `content_url` →
  `curl -sS -o NAME "<content_url>"` directly from the workspace (elevenlabsusercontent.com is allowed).
- Figma assets (fallback only): try `curl https://www.figma.com/api/mcp/asset/<id>.png`; if the proxy refuses it,
  the only route is the owner's computer (built-in browser download, then `device_stage_files` from the Downloads
  folder) — if the computer is not reachable, use ElevenLabs instead.

## 6. Timing + spec
- `ffmpeg -i voice.mp3 -af silencedetect=noise=-35dB:d=0.25 -f null -` → speech segments between silences.
- Map each script sentence/phrase to a segment, write `specs/NNN_slug.json` (format documented at the top of
  `tools/render.py`; `specs/001_krakatau.json` is the reference example):
  captions UPPERCASE with digits, key words `hl:true`; scene cuts on segment boundaries; a top `label` or
  animated `counter` in most scenes; `booms` at the hook (0.0) and at the climax word; `end` card 0.1 s after the
  voice ends; `total` = voice length + 2.1 s.

## 7. Build + check
- Render 5 stills at the busiest moments (`render.py SPEC stills ...`), look at them, fix overlaps/cut-off text.
- `bash tools/build.sh SPEC voice.mp3 videos/NNN_slug.mp4` (≈3 min). Grab 3 frames from the result and look.

## 8. Publish (owner confirms)
- Commit + push `videos/NNN_slug.mp4`, `specs/NNN_slug.json`, update `topics.md` (date, topic, title).
- Public URL: `https://raw.githubusercontent.com/bodyadantik-cyber/enciklopedia-dichi-media/main/videos/NNN_slug.mp4`
- Metricool `createScheduledPost`, blogId `8195352`, ONE post with providers tiktok + youtube (same time for both),
  time per the routine's rule (**18:00 Europe/Kiev by default**; series parts 18:00 and 21:00), **`autoPublish: true`** — Metricool publishes to both
  networks by itself, no confirmation needed. (With `autoPublish: false` TikTok only lands in the TikTok app's
  drafts/inbox and does not go public — that is why it was switched off on 23.11.2026.)
  text = caption with a comment-bait question + 6–8 hashtags (always `#энциклопедиядичи`),
  tiktokData: title ≤ 90 chars, privacyOption PUBLIC_TO_EVERYONE, isAigc true;
  youtubeData: type short, title ≤ 70 chars + " #shorts", privacy public, category EDUCATION, madeForKids false,
  isAiGeneratedContent true, 8–12 tags.
- Also send the mp4 to the owner (SendUserFile).

## 9. Report
SendUserMessage in Russian: topic, title, caption, the Metricool planner link, and anything that went wrong.
