#!/bin/bash
# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Efface uniquement les essais de la base fictive marquée et réinstalle le scénario.
exec /bin/bash "$(cd -- "$(dirname -- "$0")" && pwd)/ouvrir_demonstration.command" --reinitialiser "$@"
