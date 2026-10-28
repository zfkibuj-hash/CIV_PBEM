# Code signing: Civ4 PBEM Manager

## Goal

Windows Smart App Control / SmartScreen often blocks unsigned hobby builds. We aim to publish Authenticode-signed `Civ4PBEMManager.exe` from GitHub Actions artifacts of this public repository, ideally via [SignPath Foundation](https://signpath.org/) (free for qualifying open-source projects).

## Rules

1. **Only CI builds are signed.** Releases must come from GitHub Actions building this repository's public source (tag or approved workflow run). Ad-hoc local EXEs are not submitted for signing.
2. **No silent malware.** The app must match documented behavior (PBEM save coordination). Credential storage is local/encrypted; no hidden network endpoints beyond configured transport and optional update check.
3. **Approvals.** Signing requests require a human maintainer approval in SignPath (or equivalent) before a signed artifact is published.
4. **Transparency.** Unsigned CI artifacts may be attached for testing; signed builds are preferred for GitHub Releases.
5. **License.** The project is MIT (`LICENSE`). Signing does not change the license.

## Maintainer checklist (SignPath application)

- [x] Full `LICENSE` (MIT) in repo root
- [x] Public GitHub repository
- [x] Automated build (`.github/workflows/build.yml`)
- [x] `PRIVACY.md`
- [x] This `SIGNING.md`
- [ ] Enable **2FA** on the GitHub org/user that owns the repo
- [ ] Submit project to SignPath Foundation OSS program
- [ ] After acceptance: wire SignPath to Actions, then publish signed asset on Release

## Version metadata

The Windows EXE embeds ProductName / FileVersion from `src/config.py` via `tools/gen_version_info.py` during build.
