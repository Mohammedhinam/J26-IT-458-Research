#!/bin/zsh
# Start the existing three-model demo from the verified local checkpoints.
set -eu
cd "$(dirname "$0")/.."
if /usr/sbin/lsof -nP -iTCP:8771 -sTCP:LISTEN >/dev/null 2>&1; then
  echo 'Port 8771 is already in use. Open http://127.0.0.1:8771 and check the demo.'
  echo 'This launcher leaves the existing process untouched.'
  exit 0
fi
echo 'Open http://127.0.0.1:8771 after the model runtimes load.'
exec .venv/bin/python -B -m src.tabular.api \
  --port 8771 --local-photo-uploads \
  --vision-checkpoint models/vision_live_demo_v1/v3_best.pt \
  --roi-v1-return-zip data/vision/roi_tooth_v1_20261017/colab_return/roi_tooth_v1_colab_return.zip \
  --roi-v1-device mps \
  --roi-v2-return-zip data/vision/roi_tooth_v1_20261017/ordinal_v2/colab_return_v1_20261017/roi_tooth_v2_coral_return.zip \
  --roi-v2-device mps
