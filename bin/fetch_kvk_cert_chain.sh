#!/usr/bin/env bash
# Download the KVK API bundle and concatenate it into a PEM chain.
# usage: ./fetch_kvk_cert_chain.sh [output.pem] [zip-url]
set -euo pipefail

OUT="${1:-kvk-chain.pem}"
URL="${2:-https://developers.kvk.nl/cms/api/uploads/api_kvk_nl.zip}"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

curl -fsSL --retry 3 -o "$tmp/bundle.zip" "$URL"
unzip -qq -j -o "$tmp/bundle.zip" -d "$tmp"

# leaf -> intermediate -> root
cat "$tmp/api_kvk_nl.crt" "$tmp/DigiCertCA.crt" "$tmp/TrustedRoot.crt" > "$OUT"

openssl crl2pkcs7 -nocrl -certfile "$OUT" | openssl pkcs7 -print_certs -noout
echo "==> $OUT"
