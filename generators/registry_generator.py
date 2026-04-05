import os
import re


def _camel_to_snake_upper(name):
    s = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    s = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s)
    return s.upper()


def mod_id_to_pascal(mod_id: str) -> str:
    if '_' in mod_id:
        return ''.join(part.capitalize() for part in mod_id.split('_'))
    else:
        return mod_id.capitalize()


class RegistryGenerator:
    def __init__(self, parser, config, input_path):
        self.parser = parser
        self.config = config
        self.input_path = input_path

    def _get_mod_blocks_class(self) -> str:
        mod_id = self.config.get('mod_id', 'createplugintest')
        pascal = mod_id_to_pascal(mod_id)
        return f"{pascal}ModBlocks"

    def _get_mod_class(self) -> str:
        mod_id = self.config.get('mod_id', 'createplugintest')
        pascal = mod_id_to_pascal(mod_id)
        return f"{pascal}Mod"

    def generate(self, undo_manager=None):
        block_dir = os.path.dirname(self.input_path)
        parent_dir = os.path.dirname(block_dir)
        init_dir = os.path.join(parent_dir, self.config.get("path_init_dir", "init"))
        os.makedirs(init_dir, exist_ok=True)

        content = self._build_content()
        output_path = os.path.join(init_dir, f'{self.parser.be_registry_name}.java')

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        if undo_manager:
            undo_manager.track_created(output_path)

        return output_path

    def _build_content(self):
        p = self.parser
        cfg = self.config
        pkg = cfg['package_base']
        block_const = _camel_to_snake_upper(p.simple_name)
        be_const = block_const + '_BE'
        mod_id = cfg['mod_id']
        client_class = p.simple_name + "ClientHandler"

        # --- DEĞİŞEN KISIM ---
        mod_blocks_class = self._get_mod_blocks_class()
        # ---------------------

        return f'''package {pkg}.init;

import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.registries.DeferredRegister;
import net.neoforged.neoforge.registries.DeferredHolder;

import net.minecraft.core.registries.Registries;
import net.minecraft.world.level.block.entity.BlockEntityType;

import {pkg}.block.entity.{p.block_entity_name};
import {pkg}.client.{client_class};

public class {p.be_registry_name} {{

    public static final DeferredRegister<BlockEntityType<?>> REGISTRY =
        DeferredRegister.create(Registries.BLOCK_ENTITY_TYPE, "{mod_id}");

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<{p.block_entity_name}>> {be_const} =
        REGISTRY.register("{p.simple_name.lower()}_be", () ->
            BlockEntityType.Builder.of(
                (pos, state) -> new {p.block_entity_name}(null, pos, state),
                {mod_blocks_class}.{block_const}.get()
            ).build(null)
        );

    public static void register(IEventBus modEventBus) {{
        REGISTRY.register(modEventBus);
        {client_class}.register(modEventBus);
    }}
}}
'''