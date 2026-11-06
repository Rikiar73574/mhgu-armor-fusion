# Compendium smithy entry-hook compatibility

`compendium-smithy-forge-chain.patch` contains the complete companion source
change and its focused ARM regression test. It changes only
`compendium/mod/src/smithy.rs` and `compendium/tests/arm_native_hint.py` in the
existing Hunter's Compendium checkout. It does not change the UI, data, native
hint hook, or any caller-sensitive Armor Fusion hook.

Apply from the companion repository root, which contains both `compendium/`
and `HuntLog/`. Set these two absolute paths for your checkouts:

```sh
FUSION_ROOT=/path/to/mhgu-armor-fusion
COMPENDIUM_ROOT=/path/to/mhgu
cd "$COMPENDIUM_ROOT"
git apply --check "$FUSION_ROOT/compat/compendium-smithy-forge-chain.patch"
git apply "$FUSION_ROOT/compat/compendium-smithy-forge-chain.patch"
```

The pre-change smithy file SHA-256 is
`30598cd2001af01d1fbdcf4650732c712cae20e9cfbf8e2b6b82a47e0bf3abcd`.
The patch has context checks: if `git apply --check` fails, inspect the other
version before adapting it. A checkout that already has the change passes
`git apply --reverse --check` instead; do not apply the patch twice.

Rebuild with the companion's existing generated sources and cached toolchain.
This path does not regenerate its world data or use the network. Set
`TOOLCHAIN_ROOT` to the directory containing the cached `rustup/` and `cargo/`
directories, and ensure `rustup` and `cargo` are available on `PATH`:

```sh
TOOLCHAIN_ROOT=/path/to/mhgu-forge-work/toolchain
export RUSTUP_HOME="$TOOLCHAIN_ROOT/rustup"
export CARGO_HOME="$TOOLCHAIN_ROOT/cargo"
cd "$COMPENDIUM_ROOT/compendium/mod"
cargo +nightly build --release --locked --offline
python3 ../../HuntLog/tools/elf_to_nro.py \
  target/armv7a-none-eabi/release/libhunters_compendium.so \
  ../build/hunters_compendium.nro
python3 ../tools/check_plugin_size.py
```

The resulting NRO is `compendium/build/hunters_compendium.nro`. Install it using
the companion's normal mod directory and restart MHGURecomp. The Armor Fusion
runtime zip does not contain or replace Compendium.

The focused test executes the compiled ARM install path. It accepts the stock
prologue and aligned literal jumps to both ends of Recomp's plugin region;
it rejects unaligned, null, out-of-region, foreign branch and wrong-version
entries. Existing native-row checks run in the same test:

```sh
cd "$COMPENDIUM_ROOT"
PYTHONPATH="$COMPENDIUM_ROOT/compendium/build/test-deps" \
  python3 compendium/tests/arm_native_hint.py
```

This uses the existing Compendium test harness, its local MHGU NSO, and its
`nso.py` helper. Configure the local paths in `compendium/tests/arm_smoke.py`
for another machine, and provide Unicorn and pyelftools in the selected
interpreter or `build/test-deps`. It emulates ARM with mocked native UI calls;
it does not launch the game or establish runtime parity in both load orders.
