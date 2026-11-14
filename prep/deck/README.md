# Pitch deck builder

```bash
pip install python-pptx pillow numpy
python prep/deck/art.py OUT_ART_DIR TEAM_LOGO.webp SPACE_APPS_LOGO.png   # backgrounds and logos
python prep/deck/build_deck.py OUT_ART_DIR APP_SCREENSHOT.png docs/Field_Shift_Pitch_Deck.pptx
```

The two logo files and the app screenshot are not in the repository; pass your own copies. Every number in the deck
comes from `data/validation.json`, `web/src/data.json` and `docs/SUBMISSION.md`. If you edit the .pptx by hand,
rebuilding will overwrite your edits.
