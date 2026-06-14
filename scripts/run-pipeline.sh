#!/usr/bin/env bash
# Run the full research → storyboard → content pipeline for a brand.
# Usage: bash scripts/run-pipeline.sh <brand-slug> <content-type> "<topic>"

set -e

BRAND="${1:-example-brand}"
TYPE="${2:-carousel}"
TOPIC="${3:-5 tips for entrepreneurs}"
WORKSPACE="${AGENCY_WORKSPACE:-./workspace}"
BRANDS_DIR="${AGENCY_BRANDS_DIR:-./brands}"

echo "=== Agency Pipeline ==="
echo "Brand:    $BRAND"
echo "Type:     $TYPE"
echo "Topic:    $TOPIC"
echo "Workspace: $WORKSPACE"
echo ""

echo "--- Step 1: Research ---"
agency-research \
    --brand "$BRAND" \
    --workspace "$WORKSPACE" \
    --brands-dir "$BRANDS_DIR"

echo ""
echo "--- Step 2: Storyboard ---"
agency-storyboard \
    --brand "$BRAND" \
    --type "$TYPE" \
    --topic "$TOPIC" \
    --workspace "$WORKSPACE" \
    --brands-dir "$BRANDS_DIR"

echo ""
echo "--- Step 3: Content ---"
agency-content \
    --brand "$BRAND" \
    --platform instagram \
    --type "$TYPE" \
    --topic "$TOPIC" \
    --workspace "$WORKSPACE" \
    --brands-dir "$BRANDS_DIR"

echo ""
echo "=== Pipeline Complete ==="
echo "Check workspace outputs:"
echo "  $WORKSPACE/$BRAND/research/"
echo "  $WORKSPACE/$BRAND/storyboards/"
echo "  $WORKSPACE/$BRAND/content/"
