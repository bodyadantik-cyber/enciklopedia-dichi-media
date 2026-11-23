# «Энциклопедия дичи» — daily video pipeline

Channel: TikTok `@enciklopedia.dichi`, YouTube «энциклопедии дичи» (UCgmhWB3uri4npe9zoDaFM-w).
Language: Russian. Format: vertical 1080×1920, 30 fps, 40–55 s, documentary-thriller tone.
Owner: Kyiv time (Europe/Kiev). Publishing goes through Metricool brand `8195352`.

**Time:** the container clock is UTC even if `TZ=Europe/Kiev date` prints "Europe". Get Kyiv time with
`python3 -c "from zoneinfo import ZoneInfo;from datetime import datetime;print(datetime.now(ZoneInfo('Europe/Kyiv')))"`.

## 1. Topic
- Read `topics.md` — never repeat a used topic. **Take the next item from the Backlog first**; if a series
  Part 1 was published yesterday, today is its Part 2. Only when the backlog is empty, find new topics as below
  and refill the backlog with 5–10 ideas.
- Look at what works: vidIQ (`vidiq_instagram_tiktok_outlier_search`, `vidiq_trending_videos`, `vidiq_outliers`)
  for facts / history / science / space / mysteries in Russian and English. Windsor (`tiktok_organic`, `youtube`)
  for our own last videos' views — lean toward what performed best.
- Pick ONE surprising, verifiable fact with a strong visual story (disasters, record-breaking things, strange history,
  space, deep sea, animals, human body, lost civilisations). No politics, no medical advice, no real private people,
  no copyrighted characters.

## 2. Script (≈110–130 Russian words → ~45–50 s of speech)
- Hook in the first sentence (shock number / paradox / "this happened for real").
- 6–9 short sentences, concrete numbers, one comparison the viewer can feel, a quiet last line.
- Every number must be checked with WebSearch against ≥2 independent sources. Then spawn a separate
  fact-check agent (Agent tool, general-purpose) given ONLY the script, asking it to verify each claim with sources
  and list anything wrong. Fix everything it flags before generating audio.
- Numbers in the TTS text are written out as words; ElevenLabs eleven_v4 tags like [low, ominous], [tense],
  [whispering] are allowed.

## 3. Voice
- ElevenLabs `creative_generate_speech`, model `eleven_v4`, voice `ogi2DyUAKJb7CEdqqvlU` (Stanislav, deep RU),
  `generations_count: 1`.

## 4. Visuals (6–8 images)
- ElevenLabs (full connector, the one that has `creative_generate_image`): `creative_create_flow`, then for each image
  `creative_add_flow_node` (node_type `image-generation`, model `gpt-image-2.5-sunburst`) →
  `creative_update_node` with `model_parameters: {"aspect_ratio": "9:16", "resolution": "1K", "quality": "high"}` and the prompt →
  `creative_run_flow_nodes` with `generations_count: 1` (all image nodes in one call). Do NOT use
  `creative_generate_image` directly: it starts at 16:9 before you can set the aspect.
- Cinematic photoreal prompts, one image per beat of the story, always end with "no text".
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
  time per the routine's rule (12:00 Europe/Kiev by default), **`autoPublish: true`** — Metricool publishes to both
  networks by itself, no confirmation needed. (With `autoPublish: false` TikTok only lands in the TikTok app's
  drafts/inbox and does not go public — that is why it was switched off on 23.11.2026.)
  text = caption with a comment-bait question + 6–8 hashtags (always `#энциклопедиядичи`),
  tiktokData: title ≤ 90 chars, privacyOption PUBLIC_TO_EVERYONE, isAigc true;
  youtubeData: type short, title ≤ 70 chars + " #shorts", privacy public, category EDUCATION, madeForKids false,
  isAiGeneratedContent true, 8–12 tags.
- Also send the mp4 to the owner (SendUserFile).

## 9. Report
SendUserMessage in Russian: topic, title, caption, the Metricool planner link, and anything that went wrong.
