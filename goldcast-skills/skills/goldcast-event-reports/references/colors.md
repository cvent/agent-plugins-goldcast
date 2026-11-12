# Colors

Users can restyle the report with hex codes or a color word. The default is the Goldcast look (orange accent, purple second color). Colors apply to the artifact page and to inline visuals.

## Reading the request

| The user says | Do |
|---|---|
| Hex codes: `#0A7B5C`, `0A7B5C`, `#0af` | Normalize to `#RRGGBB` (expand 3-digit). First code is the accent. A second code, if given, is the second color (used for the second event in compare mode, and for secondary bars). |
| One color word: "green", "blue accents", "make it teal" | Use the hex from the table below as the accent. Leave the second color unset; the template derives a harmonious one. |
| Two color words: "blue and orange" | First = accent, second = second color, using the table. |
| "Our brand colors" with no values | Ask once for the hex codes. Use the default meanwhile. |
| Something unlisted ("sage", "burgundy") | Pick a sensible hex, and tell the user which one you used in one line. |
| An invalid code ("#12"), or something that isn't a color | Use the default and say so in one line. |

| Word | Hex | Word | Hex |
|---|---|---|---|
| green | `#16A34A` | teal | `#0D9488` |
| blue | `#2563EB` | pink | `#DB2777` |
| red | `#DC2626` | yellow | `#EAB308` |
| orange | `#F26B1D` | navy | `#1E3A8A` |
| purple | `#7C3AED` | gray / grey | `#64748B` |

## Applying

- **Artifact:** set `meta.accent` (and `meta.accent2` if given) in the report JSON. Nothing else changes; don't edit the template CSS.
- **Inline visuals:** use the same hex values for series fills (accent for the first event or the main series, second color for the second event).
- The template adjusts each color automatically so it stays readable on both the light and dark theme (it lightens or darkens a color that would be too faint). Tell the user if you changed a color they specified, e.g., a very pale yellow.
- Colors are for the accent only. The page background, text and the good/bad indicator colors don't change.
- Reuse the user's colors for later reports in the same conversation.
