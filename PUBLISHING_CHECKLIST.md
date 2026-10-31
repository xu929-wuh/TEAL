# Publishing Checklist

- [ ] Confirm the repository title and version.
- [ ] Run `python scripts/verify_release.py` successfully.
- [x] Create the GitHub repository at https://github.com/xu929-wuh/TEAL.
- [x] Upload this directory as the repository root.
- [ ] Confirm that the included evidence spans fit the intended source-rights scope for the selected editions.
- [ ] Confirm that no API keys, personal paths, annotator identities, or restricted files are present.
- [ ] Create a GitHub release tagged `v1.0.0`.
- [ ] Archive the release on Zenodo or an equivalent service.
- [ ] Add the archive DOI to `README.md`, `CITATION.cff`, the manuscript abstract, and the response to Reviewers A13 and Minor 6. The GitHub URL is already recorded.
- [ ] Recompute `SHA256SUMS.txt` after any post-release edits.