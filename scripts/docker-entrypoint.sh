#!/usr/bin/env bash
# Container entrypoint.
#
#   demo                fetch reference photos (first start), then the pipeline demo on :8501 (default)
#   label               fetch reference photos, then the labelling UI on :8501
#   verify              dataset integrity check (no API key, no images needed)
#   score [args]        score the committed judge results, e.g. score --split test --show-misses
#   test                unit tests
#   lint                ruff lint + format check
#   pipeline [ids]      generate → judge → retry → fallback on brief ids (needs the proxy key)
#   eval-dev|eval-test  re-judge with promptfoo (needs the proxy key and the golden images)
#   fetch               download the reference photos only
#   anything else       executed as-is (e.g. bash)

set -euo pipefail
cd /app

# Start as root only to give the app user its volumes, then re-exec everything as that user.
APP_USER=app
if [ "$(id -u)" = "0" ] && id "$APP_USER" >/dev/null 2>&1; then
  for dir in /models /app/data/products/images /app/data/runs; do
    mkdir -p "$dir"
    if [ "$(stat -c %U "$dir")" != "$APP_USER" ]; then
      chown -R "$APP_USER:$APP_USER" "$dir"
    fi
  done
  export HOME="/home/$APP_USER"
  exec setpriv --reuid="$APP_USER" --regid="$APP_USER" --init-groups "$0" "$@"
fi

streamlit() {
  exec python -m streamlit run "$1" --server.address 0.0.0.0 --server.port 8501 --server.headless true
}

fetch() {
  python scripts/fetch_products.py || echo "⚠ could not fetch some reference photos (offline?) — the apps show a placeholder instead"
}

command="${1:-demo}"
[ "$#" -gt 0 ] && shift

case "$command" in
  demo)      fetch; streamlit app/demo.py ;;
  label)     fetch; streamlit app/label.py ;;
  verify)    exec python scripts/verify.py ;;
  score)     exec python scripts/score_evals.py "$@" ;;
  test)      exec python -m pytest -q "$@" ;;
  lint)      ruff check . && exec ruff format --check . ;;
  pipeline)  fetch; exec python scripts/run_pipeline.py "$@" ;;
  eval-dev)  python scripts/build_eval_tests.py; cd evals && exec npx -y promptfoo@latest eval -c promptfoo.dev.yaml -j 6 --no-cache ;;
  eval-test) python scripts/build_eval_tests.py; cd evals && exec npx -y promptfoo@latest eval -c promptfoo.test.yaml -j 6 --no-cache ;;
  fetch)     fetch ;;
  *)         exec "$command" "$@" ;;
esac
