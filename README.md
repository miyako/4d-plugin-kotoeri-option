# 4d-plugin-kotoeri-option
4D plugin to control the defaults of Japanese IM (a.k.a. Kotoeri) on Mac

## Native string ownership audit

Audit baseline: `51c685f96770b37312859c6a53dd5f314143a75b`. Only the
first-party `Classes/C_PICTURE.cpp` helper implementation was changed. The
SDK engine implementation, headers, manifests, project files, existing
manual workflows and bundled products retain their original bytes and modes.

The compiled but command-dormant picture helpers now clear each owned path
argument exactly once, avoid allocating empty owners immediately before
shallow setters, retain the file-command output before clearing its original
argument owner, and release a created picture after retaining it into the
wrapper. `createCopy` converts the SDK's returned byte count to UTF-16 code
units. Borrowed picture arguments are still detached before cleanup; owning
copy/grayscale/thumbnail results still transfer to callers, who must dispose
them. No exported Kotoeri command or preference behavior was changed.

### Inventory and reachability

The 43 tracked native files comprise the following exhaustive groups. Names
with `.cpp/.h` denote both tracked files under `4D Plugin API/Classes/`.

| Files | Build/include reachability and ownership findings |
|---|---|
| `4DPlugin.cpp`, `4DPlugin.h` | `PluginMain` dispatches selectors 1 and 2 to `Kotoeri_Get_option` and `Kotoeri_SET_OPTION`. Both copy borrowed text parameters; owned NSString keys/values and copied CF preference results are released after use. The getter copies content before releasing the CF value. The pre-existing catch-all remains unchanged. |
| `C_TEXT.cpp/.h` | Used by both commands. Owns a C++ UTF-16 string, copies parameter descriptors by explicit length, and writes via the content setter, not descriptor transfer. NSString copy/path/URL and UTF conversion helpers were included in inspection; path helpers are dormant in these commands. Copying of the wrapper is already disabled. |
| `C_LONGINT.cpp/.h` | Used for setter's type argument; numeric value storage, no string owner. |
| `C_PICTURE.cpp/.h` | Includes `CPicture` and forwarding `C_PICTURE`; compiled, not called by either command. Internal synchronous procedure IDs: read picture 678, convert 1002, transform 988, properties 457, thumbnail 679. Fixed owners/lengths described above. Native-image and successful picture-format metadata paths are not certified by the synthetic shim. |
| `ARRAY_TEXT.cpp/.h` | Compiled/dormant. Copies borrowed elements into independent C++ strings before replacement; creates a separate descriptor for each accepted output and does not dispose it after transfer. Allocation-failure limitations below remain deferred. |
| `C_POINTER.cpp/.h` | Compiled/dormant. Pointer/reference metadata handling is ambiguous: `getVariable` interprets a `PA_GetPointerValue` union as definition metadata. Do not clear the result and relabel its union as borrowed metadata; no speculative ownership change was made. |
| `C_BLOB.cpp/.h` | Compiled/dormant, includes `CBytes`, hex/base64 text conversions and engine handle handoffs. General byte-buffer/handle allocation-failure policy is outside this string fix and remains deferred. |
| `C_DATE.cpp/.h`, `C_INTEGER.cpp/.h`, `C_REAL.cpp/.h`, `C_TIME.cpp/.h` | Compiled/dormant scalar value wrappers, no descriptor ownership operations. |
| `ARRAY_BOOLEAN.cpp/.h`, `ARRAY_DATE.cpp/.h`, `ARRAY_INTEGER.cpp/.h`, `ARRAY_LONGINT.cpp/.h`, `ARRAY_REAL.cpp/.h`, `ARRAY_TIME.cpp/.h` | Compiled/dormant value-array wrappers; no string descriptor handoff. Their shared SDK array allocation/resize failure boundary is not certified. |
| `4D Plugin API/4DPluginAPI.c`, `4DPluginAPI.h`, `EntryPoints.h`, `Flags.h`, `PrivateTypes.h`, `PublicTypes.h`, `4DPluginAPI.def` | Bundled SDK engine wrapper, all transitive declarations/layouts/selectors and Windows export list. Exported `FourDPackex` stores the engine callback and invokes `PluginMain`; `.def` exports `FourDPackex`. No JSON API or first-party JSON path exists in these sources. |
| `4D Plugin_Prefix.pch`, `4D Plugin API/Classes/C_TYPES.h` | Carbon prefix and platform/Cocoa/standard string/vector typedef includes. |

`Kotoeri Option.xcodeproj/project.pbxproj` compiles the complete SDK `.c`,
`4DPlugin.cpp` and all 16 class `.cpp` files as Objective-C++. All class
headers are included by `4DPluginAPI.h`. The legacy `.vcxproj` lists the
16 class sources and entry source, but has no SDK `.c` compile item and the
entry code uses macOS APIs; it is not evidence of working Windows support.
Both source and bundled manifests declare only `Kotoeri Get option(&T):T`
and `Kotoeri SET OPTION(&T;&T;&L)`. Scalar signatures were not used to exclude
the compiled/dormant helpers from inspection.

### Contracts and immutable provenance

Canonical guidance: `miyako/skills`, commit
`e6b492fcb81e5e1a7f7db723594b420e63bf6eb9`,
`4d-skills/skills/4dplugin/SKILL.md`. The local SDK `.c` blob is
`bdb2e7894e66d5abf3ebfedb41aa4e47739e2fc6`, last introduced at root by
`fccb2a52a1f4e919cc59c42beb2da53d245c0c8a`. Its `v14` implementation and
`v13` header comments are not verified upstream SDK release identifiers.
The pinned baseline tree supplies immutable local provenance for all SDK
headers, layouts and wrapper sources.

In this exact SDK, `PA_SetStringInArray` disposes the old element and
shallow-transfers the new descriptor only for Unicode arrays with non-null
data, a non-null input descriptor and `0 <= index <= count` (including zero).
Rejected inputs remain caller-owned. `PA_GetStringInArray` returns a borrowed
alias. `PA_SetStringVariable` and `PA_SetPictureVariable` shallow-assign and
do not dispose previous owners; creating string/picture variables first
allocates empty owners. `PA_ClearVariable` forwards owner cleanup to 4D.
`PA_SetUnistring`/`PA_ReturnString` instead use the engine content setter.
`PA_DuplicatePicture(p, 1)` retains; conversion sizes and results are bytes,
whereas `PA_Unistring.fLength` is UTF-16 units excluding the terminator.

The command wrapper's handle-allocation failure returns raw `fType == 0`;
`PA_GetVariableKind` misleadingly normalizes it to string. The method wrapper
instead returns Undefined. The picture procedures do not consume their
function-return value, so the fix neither reads/clears failed sentinels nor
invents owning function results for procedures. Failed picture-data getters
are checked for error before their descriptor is examined.

### Safe regression and limits

Run on macOS, with output outside tracked products:

```sh
python3 .github/tests/test_ownership.py --baseline --output /tmp/kotoeri-ownership
```

This compiles the actual final entry source, all 16 helper sources and the
complete unchanged SDK, not a rewritten extraction. A forced-include boundary
replaces preference reads/writes/synchronization and blocks URL-path/logging
boundaries before compilation; the executable's imports are checked too.
Every engine callback is synthetic and unexpected selectors fail closed.
Only in-memory Foundation/CF text operations use real framework code.
No actual input method, preferences, user plist, filesystem picture read,
keyboard monitoring/injection, UI activation, signing, packaging or release
dispatcher is used. Even the real Kotoeri dispatcher is exercised only with
these already-installed stubs and synthetic text.

The same harness is compiled against an immutable `git archive` of the
baseline. It verifies all original tracked file bytes and executable modes
except the intentional picture-helper and README edits. Harness reference
paths were verified through GitHub tree/contents at immutable revisions:
`miyako/4d-plugin-jpegoptim`
`e49adcd32bd5500cf3de680faa3649b32463ff5e`
(`.github/tests/ownership_host.mm`, `test_ownership.py`) and
`miyako/4d-plugin-jsmin`
`d12035643f874ec57ae634194ec0f1206b05a5f2`
(`tests/ownership/host.mm`, `run.py`); contracts were independently adapted.

Expected differential: **64 fixed passes; baseline 20 control passes and
44 named defect failures**. Baseline ASCII `createCopy` must specifically
report ASan heap-buffer-overflow, path cleanup must report duplicate cleanup
or an extra retained owner, and the other picture paths must report their
specific reference/owner imbalance. Coverage includes ASCII, BMP,
supplementary and empty text; allocated and null empty descriptors; exact
UTF-8 bytes/UTF-16 units/capacity/termination; independent array outputs,
borrowed copies, replacement/shrink/clear and rejected type/index/data/null
assignments; scalar content-setter controls; owning picture handoff survival;
borrowed picture input; poisoned failed getter/command outputs; and command
handle failure. ASan and UBSan run without alignment exclusions; packed SDK
members are copied before passing them to reference-taking test containers.
macOS LSan is unavailable, so every successful case explicitly requires
`strings=0 pictures=0 handles=0`.

**Deferred, not fixed or certified:** initial string/array/picture allocation
failure and converter failure require a defined error/preservation policy at
the existing void/API boundary. `ARRAY_TEXT::toParamAtIndex` can publish its
new array kind without validating creation; an unsuccessful insertion can
leave a created string caller-owned without cleanup. The SDK's
`PA_ResizeArray` also updates count even when `PA_SetHandleSize` fails; normal
array passes do not certify OOM safety. No success-shaped fallback was added
and no failure-preservation claim is made. SDK-only application/structure/
preferences path strings, successful picture-format strings, pointer metadata
ownership, and non-string/CBytes allocation failures need stronger host
contracts and remain unchanged. No real 4D host, Windows, actual IM operation
or original Windows Poppler crash was executed or certified.

The scoped **Native ownership** workflow runs unsigned synthetic regressions
on `macos-latest`. Existing version-bump and signed release workflows remain
manual-only and unchanged.

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
