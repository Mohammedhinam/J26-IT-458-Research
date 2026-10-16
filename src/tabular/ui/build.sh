#!/bin/sh
# Run from repository root. Dependencies stay in ignored data/, never global.
set -eu
mkdir -p data/component2_ui_dependencies_v2
cp src/tabular/ui/package.json data/component2_ui_dependencies_v2/package.json
cp src/tabular/ui/package-lock.json data/component2_ui_dependencies_v2/package-lock.json
npm ci --prefix data/component2_ui_dependencies_v2 --ignore-scripts --no-audit --no-fund
NODE_PATH="$PWD/data/component2_ui_dependencies_v2/node_modules" 
export NODE_PATH
data/component2_ui_dependencies_v2/node_modules/.bin/esbuild src/tabular/ui/App.jsx --bundle --minify --outfile=src/tabular/ui/app.js --define:process.env.NODE_ENV='"production"' --legal-comments=external
