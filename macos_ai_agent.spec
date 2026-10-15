# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller recipe for the macOS AI Agent application bundle."""

from PyInstaller.utils.hooks import collect_all, copy_metadata

block_cipher = None

datas = []
binaries = []
hiddenimports = []

# These packages use dynamic imports or load native resources that PyInstaller
# cannot always discover from static analysis alone.
for package in (
    "av",
    "langchain_groq",
    "langgraph",
    "langgraph.checkpoint.sqlite",
    "sounddevice",
):
    package_datas, package_binaries, package_hiddenimports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports

# Keep distribution metadata available to libraries that read their version
# information at runtime.
for distribution in (
    "av",
    "groq",
    "langchain-groq",
    "langgraph",
    "langgraph-checkpoint-sqlite",
    "PySide6",
    "sounddevice",
):
    datas += copy_metadata(distribution)

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="macOS AI Agent",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
app = BUNDLE(
    exe,
    name="macOS AI Agent.app",
    icon=None,
    bundle_identifier="com.github.mozzam123.macos-ai-agent",
    info_plist={
        "CFBundleDisplayName": "macOS AI Agent",
        "CFBundleName": "macOS AI Agent",
        "NSMicrophoneUsageDescription": (
            "macOS AI Agent records your voice after you use its hotkey."
        ),
        "NSAppleEventsUsageDescription": (
            "macOS AI Agent automates macOS apps only for actions you request."
        ),
        "NSHighResolutionCapable": True,
    },
)
