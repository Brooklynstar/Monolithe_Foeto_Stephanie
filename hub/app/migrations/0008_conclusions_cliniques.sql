-- SPDX-License-Identifier: CC-BY-NC-SA-4.0
CREATE TABLE conclusions_cliniques (
    dossier TEXT PRIMARY KEY REFERENCES dossiers(numero) ON DELETE CASCADE,
    texte TEXT NOT NULL
);
