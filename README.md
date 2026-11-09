# 4d-plugin-kotoeri-option
4D plugin to control the defaults of Japanese IM (a.k.a. Kotoeri) on Mac

##Platform

| carbon | cocoa | win32 | win64 |
|:------:|:-----:|:---------:|:---------:|
|🆗|🆗|🚫|🚫|

Commands
---

```c
// --- Kotoeri
Kotoeri_Get_option
Kotoeri_SET_OPTION
```

Example
---

```
  //"1" kana, "0" romaji
$isKana:=Kotoeri Get option ("JIMPrefTypingMethodKey")

Kotoeri SET OPTION ("JIMPrefTypingMethodKey";Choose($isKana="1";"0";"1");Is integer)

  //for more keys see
  //http://baqamore.hatenablog.com/entry/2015/02/09/221934

  //note: change takes effect after window switch or focus event
```

## Manual versioning and publication

The workflows are independent manual operations (pattern A). Neither a source
push nor a tag push starts Build.

1. Run **Bump version**, explicitly selecting the destination branch in Actions
   and choosing `patch`, `minor`, or `major`. It checks out the immutable selected
   commit, validates clean source and the remote branch, and commits only source
   metadata. A nonforce push disables tag following explicitly. The mandatory
   executable pre-push guard requires the server-advertised old branch SHA to
   equal the selected SHA, rejecting late advances, rewinds, deletions and
   same-result races. A missing/nonexecutable guard fails closed.
2. Separately run **Build** on the desired branch. It has no inputs; every job
   checks out the selected `github.sha`, not a moving branch or a typed tag.
   Source metadata must remain unchanged from that commit, including at the
   final publication check. Strict source `X.Y.Z` determines `vX.Y.Z` and the
   asset names.

`MARKETING_VERSION` in all three project configurations is the authority.
`CURRENT_PROJECT_VERSION`, source `Info.plist` version fields (when present),
and `English.lproj/InfoPlist.strings` are coordinated with it. Supported Xcode
references are preserved; absent `CFBundleVersion` stays absent. The old bump
header promised coordinated marketing/project versions, but its implementation
only updated marketing: the 1.0.1 and 1.0.2 bump commits left the project version
at 1.0.0, and localized source still said 1.0. This migration repairs only those
fields to the existing 1.0.2 authority, without a release-version increment.
Bundled/prebuilt metadata, Windows project files, 4D data, dependency and schema
versions are not source version inputs and are not rewritten.

Build preserves the macOS universal arm64/x86_64 build, architecture check,
Developer ID signing and strict verification, ZIP/DMG packaging, both notary
submissions and DMG stapling. There is no Windows CI build or external native
dependency installation. The existing Apple/notary secret names are unchanged.
Assets remain `Kotoeri Option-X.Y.Z.zip` and `Kotoeri Option-X.Y.Z.dmg`.

Publication is serialized repository-wide across branches. Before native work
and again immediately after all required gates, authenticated, explicitly
paginated release-list requests check every page, including drafts, and remote
tags are checked. API/auth/network/404/malformed responses fail closed; only a
complete successful no-match permits publication. It creates a new exact-SHA
tag with POST git/refs (even a same-SHA concurrent creation fails), verifies the
remote SHA, then POSTs a public non-prerelease with an empty body and no generated
notes. Assets are POSTed separately to the newly returned release ID.

### Failure recovery

Publication never updates, deletes, overwrites, rolls back or retries remote
state. On any failure, inspect the Actions error, selected SHA, tag, release ID
and accepted assets. A tag, public release or partial upload may remain, even
when a request's response was lost. Do not blindly rerun: existing tags or draft/
published releases block publication. A maintainer must investigate and decide
manual recovery outside these workflows; a failed upload leaves the public
release and already accepted assets intact.

### Local regression checks

Run `python3 -m unittest discover -s .github/tests -v` and `actionlint`.
Tests use source copies, mocked API responses and isolated bare Git remotes;
they do not execute native/signing tools or publish real tags/releases.
The lifecycle helpers and tests adapt the reviewed
`miyako/4d-plugin-script#1` implementation at
`4cdf7b5d4ec645385654e6cb17a2ff0603925fb5` to this repository's three
configurations, localized product text, macOS-only jobs and asset names.
