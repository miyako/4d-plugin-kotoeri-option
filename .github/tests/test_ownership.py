#!/usr/bin/env python3
"""Synthetic ownership regression; never build a plugin bundle or call real preferences."""

import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
BASELINE = "51c685f96770b37312859c6a53dd5f314143a75b"
SDK_BLOB = "bdb2e7894e66d5abf3ebfedb41aa4e47739e2fc6"
FIXTURE_TEXTS = ("ASCII", "\u65e5", "\U0001f600", "")
CASES = (
    [(case, text, empty)
     for case in ("path", "copy", "scalar", "dispatcher")
     for text in FIXTURE_TEXTS for empty in ("allocated", "null")]
    + [(case, "", empty)
       for case in ("bytes", "gray", "size", "thumbnail", "arrays", "borrowed")
       for empty in ("allocated", "null")]
    + [(case + suffix, "", empty)
       for case in ("path", "copy", "gray", "size", "thumbnail")
       for suffix in ("-handle-failure", "-command-failure")
       for empty in ("allocated", "null")]
)


def build(source, binary):
    api = source / "4D Plugin API"
    sdk = (api / "4DPluginAPI.c").read_bytes()
    blob = hashlib.sha1(f"blob {len(sdk)}\0".encode() + sdk).hexdigest()
    if blob != SDK_BLOB:
        raise AssertionError("Re-audit the bundled SDK before changing its pinned blob")
    command = [
        "clang++", "-std=c++14", "-x", "objective-c++",
        "-include", str(ROOT / ".github/tests/ownership_boundary.h"),
        "-I", str(api), "-I", str(api / "Classes"),
        "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
        "-fno-omit-frame-pointer", "-g", "-O1",
        "-Wno-deprecated-declarations", "-Wno-return-type-c-linkage",
        "-Wno-ignored-attributes", "-Wno-writable-strings",
        "-Wno-logical-op-parentheses",
        str(api / "4DPluginAPI.c"), str(source / "4DPlugin.cpp"),
        *map(str, sorted((api / "Classes").glob("*.cpp"))),
        str(ROOT / ".github/tests/ownership_host.mm"),
        "-framework", "Cocoa", "-framework", "Carbon", "-o", str(binary),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    imports = subprocess.check_output(["nm", "-u", str(binary)], text=True)
    for symbol in ("_CFPreferences", "_CFURLCreateWithFileSystemPath",
                   "_CFURLCopyFileSystemPath", "_NSLog"):
        if symbol in imports:
            raise AssertionError(f"Unsafe platform boundary remains linked: {symbol}")


def run_cases(binary, logs, baseline=False):
    logs.mkdir(parents=True, exist_ok=True)
    passed = failed = 0
    for number, (case, text, empty) in enumerate(CASES):
        result = subprocess.run(
            [str(binary), case, text, empty], capture_output=True, text=True,
            env={**os.environ, "ASAN_OPTIONS": "detect_leaks=0",
                 "UBSAN_OPTIONS": "halt_on_error=1"},
        )
        output = result.stdout + result.stderr
        (logs / f"{number:02d}-{case}-{empty}.log").write_text(output)
        defect = case.split("-")[0] not in ("arrays", "scalar", "dispatcher", "borrowed")
        expected_failure = baseline and defect
        if bool(result.returncode) != expected_failure:
            raise AssertionError(f"Unexpected {case}/{text!r}/{empty}:\n{output}")
        if expected_failure:
            family = case.split("-")[0]
            markers = {
                "path": ("duplicate/unowned string disposal", "return must independently retain"),
                "copy": ("unbalanced picture references", "unbalanced string allocations",
                         "AddressSanitizer: heap-buffer-overflow"),
                "bytes": ("return must independently retain",),
                "gray": ("unbalanced picture references",),
                "size": ("unbalanced picture references",),
                "thumbnail": ("unbalanced picture references",),
            }[family]
            if family == "copy" and text == "ASCII":
                markers = ("AddressSanitizer: heap-buffer-overflow",)
            if not any(marker in output for marker in markers):
                raise AssertionError(f"Wrong baseline failure for {case}:\n{output}")
            failed += 1
            print(f"EXPECTED BASELINE FAILURE {case}/{text!r}/{empty}", flush=True)
        else:
            if "strings=0 pictures=0 handles=0" not in output:
                raise AssertionError(output)
            passed += 1
            print(f"PASS {case}/{text!r}/{empty}", flush=True)
    print(f"{'baseline' if baseline else 'fixed'}: {passed} passed, {failed} expected failures")


def compare_baseline(baseline):
    exemptions = {"4D Plugin API/Classes/C_PICTURE.cpp", "README.md"}
    tracked = subprocess.check_output(
        ["git", "ls-tree", "-r", "-z", BASELINE], cwd=ROOT,
    ).decode().split("\0")
    for entry in filter(None, tracked):
        metadata, name = entry.split("\t", 1)
        mode = metadata.split()[0]
        if name not in exemptions and (baseline / name).read_bytes() != (ROOT / name).read_bytes():
            raise AssertionError(f"Unexpected baseline file modification: {name}")
        if bool((ROOT / name).stat().st_mode & 0o111) != (mode == "100755"):
            raise AssertionError(f"Unexpected file mode change: {name}")


class OwnershipTests(unittest.TestCase):
    @unittest.skipUnless(os.uname().sysname == "Darwin", "macOS synthetic text host")
    def test_actual_sources(self):
        with tempfile.TemporaryDirectory(prefix="kotoeri-ownership-") as directory:
            output = Path(directory)
            binary = output / "fixed"
            build(ROOT, binary)
            run_cases(binary, output / "logs")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    build(ROOT, args.output / "fixed")
    run_cases(args.output / "fixed", args.output / "fixed-logs")
    if args.baseline:
        with tempfile.TemporaryDirectory(prefix="kotoeri-baseline-") as directory:
            baseline = Path(directory)
            archive = baseline / "baseline.tar"
            with archive.open("wb") as stream:
                subprocess.run(["git", "archive", BASELINE], cwd=ROOT, stdout=stream, check=True)
            with tarfile.open(archive) as source:
                source.extractall(baseline, filter="data")
            compare_baseline(baseline)
            build(baseline, args.output / "baseline")
            run_cases(args.output / "baseline", args.output / "baseline-logs", baseline=True)


if __name__ == "__main__":
    main()
