#!/usr/bin/env bash
# Full build: bash build.sh SPEC.json VOICE.mp3 OUT.mp4
# Renders video in 2 parallel halves, makes the SFX bed, mixes voice (ducking) to -14 LUFS,
# and writes a ~25 MB H.264 file ready for TikTok / YouTube Shorts.
set -euo pipefail
SPEC="$1"; VOICE="$2"; OUT="$3"
DIR="$(cd "$(dirname "$0")" && pwd)"
TOTAL=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['total'])" "$SPEC")
FR=$(python3 -c "print(int(round($TOTAL*30)))"); HALF=$((FR/2))
python3 "$DIR/render.py" "$SPEC" render 0 $HALF partA.tmp.mp4 & P1=$!
python3 "$DIR/render.py" "$SPEC" render $HALF $FR partB.tmp.mp4 & P2=$!
python3 "$DIR/audio.py" "$SPEC" bed.wav
wait $P1; wait $P2
mv partA.tmp.mp4 partA.mp4; mv partB.tmp.mp4 partB.mp4
printf "file 'partA.mp4'\nfile 'partB.mp4'\n" > list.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i list.txt -i "$VOICE" -i bed.wav -filter_complex \
"[1:a]aresample=48000,pan=stereo|c0=c0|c1=c0,highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,volume=2.0,asplit=2[v][vsc];[2:a]volume=0.55[b];[b][vsc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=300[bd];[v][bd]amix=inputs=2:normalize=0:duration=longest,loudnorm=I=-14:TP=-1.5:LRA=9[a]" \
-map 0:v -map "[a]" -c:v libx264 -preset slow -crf 24 -maxrate 4M -bufsize 8M -pix_fmt yuv420p \
-c:a aac -b:a 192k -t "$TOTAL" -movflags +faststart out.tmp.mp4
mv out.tmp.mp4 "$OUT"
ls -la "$OUT"
