#!/bin/zsh
# Keep the earlier port-8771 server intact. Run the proposal candidate on 8773.
set -eu
cd "$(dirname "$0")/.."
if /usr/sbin/lsof -nP -iTCP:8773 -sTCP:LISTEN >/dev/null 2>&1; then
  echo 'Port 8773 is already in use. Check http://127.0.0.1:8773/.'
  exit 0
fi
exec .venv/bin/python -B -m src.tabular.api \
  --port 8773 --local-photo-uploads \
  --efficientnet-checkpoint data/efficientnet_adaptation_v1_20261017_1792202682936988000/fold0_last_block/final.pt \
  --vision-checkpoint models/vision_live_demo_v1/v3_best.pt \
  --roi-v1-return-zip data/vision/roi_tooth_v1_20261017/colab_return/roi_tooth_v1_colab_return.zip \
  --roi-v1-device mps \
  --roi-v2-return-zip data/vision/roi_tooth_v1_20261017/ordinal_v2/colab_return_v1_20261017/roi_tooth_v2_coral_return.zip \
  --roi-v2-device mps
