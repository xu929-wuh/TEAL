# Publishing Checklist

- [ ] Confirm the repository title and version.
- [ ] Run `python scripts/verify_release.py` successfully.
- [ ] Create a new GitHub repository, for example `teal-evidence-audit-subset`.
- [ ] Upload this directory as the repository root.
- [ ] Confirm that the included evidence spans fit the intended source-rights scope for the selected editions.
- [ ] Confirm that no API keys, personal paths, annotator identities, or restricted files are present.
- [ ] Create a GitHub release tagged `v1.0.0`.
- [ ] Archive the release on Zenodo or an equivalent service.
- [ ] Add the GitHub URL and archive DOI to `CITATION.cff`, the manuscript Data and Code Availability statement, and the response to Reviewers A13 and Minor 6.
- [ ] Recompute `SHA256SUMS.txt` after any post-release edits.