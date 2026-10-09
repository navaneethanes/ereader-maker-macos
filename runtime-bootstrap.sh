#!/bin/zsh
# SPDX-License-Identifier: AGPL-3.0-only
# Installs into a private, versioned directory; never uses the system Python.
set -eu
resources="${0:A:h}"
support="${1:?Application Support directory required}"
architecture="$(uname -m)"
case "$architecture" in
  arm64)
    runtime_url='https://github.com/astral-sh/python-build-standalone/releases/download/20261003/cpython-3.12.15%2B20261003-aarch64-apple-darwin-install_only.tar.gz'
    runtime_sha='316a463172740e71d8dca1f2730784e325f3f720941137b5d674d5801a632213' ;;
  x86_64)
    runtime_url='https://github.com/astral-sh/python-build-standalone/releases/download/20261003/cpython-3.12.15%2B20261003-x86_64-apple-darwin-install_only.tar.gz'
    runtime_sha='a8fd7a91852f19b6d959793ef41fad048631ccb2a334a9ecdf573255298f7978' ;;
  *) echo 'Unsupported Mac architecture.' >&2; exit 1 ;;
esac
lock_sha="$(/usr/bin/shasum -a 256 "$resources/requirements-runtime.txt")"
lock_sha="${lock_sha%% *}"
final="$support/runtime-v1-$architecture-${lock_sha:0:12}"
if [[ -f "$final/.ready" && -x "$final/python/bin/python3" ]]; then exit 0; fi
mkdir -p "$support"
chmod 700 "$support"
if ! mkdir "$support/.setup-lock" 2>/dev/null; then
  echo 'Setup is already running. If it was interrupted, quit the app and remove .setup-lock from its Application Support folder.' >&2
  exit 1
fi
stage="$(mktemp -d "$support/.setup-XXXXXX")"
trap 'rm -rf "$stage"; rmdir "$support/.setup-lock" 2>/dev/null || true' EXIT
trap 'exit 130' INT TERM
print 'Downloading the private conversion runtime…'
/usr/bin/curl --fail --location --proto '=https' --tlsv1.2 --connect-timeout 20 --max-time 600 --retry 2 --silent --show-error "$runtime_url" -o "$stage/runtime.tar.gz"
actual="$(/usr/bin/shasum -a 256 "$stage/runtime.tar.gz")"
if [[ "${actual%% *}" != "$runtime_sha" ]]; then echo 'Runtime checksum mismatch. Setup stopped.' >&2; exit 1; fi
print 'Verified download. Preparing conversion tools…'
/usr/bin/tar -xzf "$stage/runtime.tar.gz" -C "$stage"
rm "$stage/runtime.tar.gz"
unset PYTHONHOME PYTHONPATH
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
"$stage/python/bin/python3" -m pip --isolated install --disable-pip-version-check --no-cache-dir --require-hashes --only-binary=:all: --index-url https://pypi.org/simple -r "$resources/requirements-runtime.txt"
"$stage/python/bin/python3" -m pip check
"$stage/python/bin/python3" -c 'import pymupdf, mammoth, PIL, markdown, bs4, defusedxml'
# An incomplete directory from a previous version is never treated as ready.
if [[ -e "$final" ]]; then echo 'An incomplete runtime exists. Use the repair instructions in INSTALL.md.' >&2; exit 1; fi
touch "$stage/.ready"
mv "$stage" "$final"
print 'Ready to convert. Future launches work offline.'
