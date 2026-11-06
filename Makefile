BUILD := build
GAME_DIR ?= game
PYTHON ?= python3
ARM_PYTHON ?= python3
ARM_FLAGS := --target=armv7a-none-eabi -marm -march=armv7-a -mfpu=vfpv3-d16 -mfloat-abi=softfp -std=c11 -O2 -fPIC -ffreestanding -fno-builtin -fno-stack-protector -fno-unwind-tables -Wall -Wextra -Werror -Isrc -I$(BUILD)
SOURCES := src/bootstrap.c src/bridge.c src/armor_fusion.c src/hle/armorfusion.c
OBJECTS := $(patsubst src/%.c,$(BUILD)/%.o,$(SOURCES)) $(BUILD)/bridge_entry.o $(BUILD)/start.o
all: $(BUILD)/armor_fusion.nro
$(BUILD):
	mkdir -p $@
$(BUILD)/catalog-inputs.json: FORCE tools/catalog_inputs.py tools/fusion_materials.py | $(BUILD)
	$(PYTHON) tools/catalog_inputs.py "$(GAME_DIR)/romfs/nativeNX/table" $@
$(BUILD)/armor-fusion.afus: $(BUILD)/catalog-inputs.json tools/fusion_materials.py
	$(PYTHON) tools/fusion_materials.py "$(GAME_DIR)/romfs/nativeNX/table" --output $(BUILD)/catalog.json --binary $@
$(BUILD)/catalog.inc: $(BUILD)/armor-fusion.afus tools/embed_catalog.py
	$(PYTHON) tools/embed_catalog.py $< $@
$(BUILD)/armor_fusion.o: $(BUILD)/catalog.inc
$(BUILD)/%.o: src/%.c src/rt.h src/hle.h src/armor_fusion.h
	mkdir -p $(dir $@)
	clang $(ARM_FLAGS) -c $< -o $@
$(BUILD)/bridge_entry.o: src/bridge.S | $(BUILD)
	clang --target=armv7a-none-eabi -marm -c $< -o $@
$(BUILD)/start.o: link/start.S | $(BUILD)
	clang --target=armv7a-none-eabi -marm -c $< -o $@
$(BUILD)/armor_fusion.elf: $(OBJECTS) link/plugin.ld link/exports.map
	ld.lld -shared -T link/plugin.ld --version-script=link/exports.map --hash-style=sysv --build-id=sha1 -o $@ $(OBJECTS)
$(BUILD)/armor_fusion.nro: $(BUILD)/armor_fusion.elf tools/elf_to_nro.py
	$(PYTHON) tools/elf_to_nro.py $< $@
$(BUILD)/test_bridge_fixture.o: tests/test_bridge_fixture.c src/rt.h src/hle.h | $(BUILD)
	clang $(ARM_FLAGS) -c $< -o $@
$(BUILD)/test_bridge.elf: $(BUILD)/bridge.o $(BUILD)/bridge_entry.o $(BUILD)/start.o $(BUILD)/bootstrap.o $(BUILD)/armor_fusion.o $(BUILD)/hle/armorfusion.o $(BUILD)/test_bridge_fixture.o link/plugin.ld link/tests.map
	ld.lld -shared -T link/plugin.ld --version-script=link/tests.map --hash-style=sysv -o $@ $(filter %.o,$^)
test: | $(BUILD)
	cc -std=c11 -Wall -Wextra -Werror -DFUSION_CATALOG_NO_EMBED -iquote src tests/test_policy.c src/armor_fusion.c -o $(BUILD)/test_policy
	$(BUILD)/test_policy
	$(PYTHON) -m unittest discover -s tools -p 'test_*.py' -v
	$(PYTHON) -m unittest discover -s tests -p 'test_package.py' -v
test-arm: $(BUILD)/test_bridge.elf $(BUILD)/armor_fusion.elf
	$(ARM_PYTHON) tests/test_bridge_arm.py
clean:
	rm -rf $(BUILD)
FORCE:
.PHONY: all test test-arm clean FORCE
