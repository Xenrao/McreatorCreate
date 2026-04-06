import os
import re

def camel_to_snake_upper(name):
    s = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    s = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s)
    return s.upper()

def mod_id_to_pascal(mod_id: str) -> str:
    """
    bruhmoment   -> Bruhmoment
    bruh_moment  -> BruhMoment
    bruh_Moment  -> BruhMoment  (snake_case ise her parçayı capitalize et)
    """
    if '_' in mod_id:
        return ''.join(part.capitalize() for part in mod_id.split('_'))
    else:
        return mod_id.capitalize()

class EntityGenerator:
    def __init__(self, transformer, config, input_path):
        self.transformer = transformer
        self.config = config
        self.input_path = input_path
        self.parser = transformer.parser

    def _get_mod_blocks_class(self) -> str:
        """Config'deki mod_id'den ModBlocks sınıf adını üretir."""
        mod_id = self.config.get('mod_id', 'Createplugintest')
        pascal = mod_id_to_pascal(mod_id)
        return f"{pascal}ModBlocks"

    def generate(self, undo_manager=None):
        block_dir = os.path.dirname(self.input_path)
        entity_dir = os.path.join(block_dir, 'entity')
        os.makedirs(entity_dir, exist_ok=True)

        content = self._build_content()
        output_path = os.path.join(entity_dir, f'{self.parser.block_entity_name}.java')

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        if undo_manager:
            undo_manager.track_created(output_path)

        return output_path

    def _build_content(self):
        if self.config['is_generator']:
            return self._generator_entity()
        else:
            return self._impact_entity()

    def _get_tick_imports_str(self):
        if not hasattr(self.transformer, 'tick_imports'):
            return ''
        if not self.transformer.tick_imports:
            return ''
        return '\n' + '\n'.join(self.transformer.tick_imports)

    def _tick_section(self):
        return ''
#        if not self.transformer.tick_body:
#            return ''
#
#        converted_lines = []
#        for line in self.transformer.tick_body:
#            stripped = line.strip()
#
#            if stripped.startswith('super.tick('):
#                continue
#
#            converted = line
#            converted = converted.replace('world,', 'this.level,')
#            converted = converted.replace('world.', 'this.level.')
#            converted = converted.replace(', world)', ', this.level)')
#            converted = converted.replace('(world)', '(this.level)')
#            converted = converted.replace('pos.getX()', 'this.getBlockPos().getX()')
#            converted = converted.replace('pos.getY()', 'this.getBlockPos().getY()')
#            converted = converted.replace('pos.getZ()', 'this.getBlockPos().getZ()')
#            converted = converted.replace('blockstate', 'this.getBlockState()')
#            converted = converted.replace(', pos)', ', this.getBlockPos())')
#            converted = converted.replace('(pos)', '(this.getBlockPos())')
#            converted = converted.replace('pos,', 'this.getBlockPos(),')
#            converted = converted.replace('random', 'this.level.random')
#
#            converted_lines.append('        ' + converted.strip())
#
#        tick_lines = '\n'.join(converted_lines)
#        return (
#            '\n'
#            '    @Override\n'
#            '    public void tick() {\n'
#            '        super.tick();\n'
#            '        tickCounter++;\n'
#            '        if (tickCounter % tickTrigger == 0) {\n'
#            f'    {tick_lines}\n'
#            '        }\n'
#            '    }\n'
#        )

    def _goggle_section(self):
        if not self.config.get('use_goggle_override'):
            return ''
        return (
            '\n'
            '    @Override\n'
            '    public boolean addToGoggleTooltip(List<Component> tooltip, boolean isPlayerSneaking) {\n'
            '        // TODO: Add goggle tooltip content\n'
            '        return super.addToGoggleTooltip(tooltip, isPlayerSneaking);\n'
            '    }\n'
        )
    
    def _procedure_section(self):
        procedure = self.config.get('procedure')
        if procedure:
            return (
                f'{procedure}Procedure.execute(this.level, this.getBlockPos().getX(), this.getBlockPos().getY(), this.getBlockPos().getZ(), this.getBlockState());'
            )
        return ''

    def _generator_entity(self):
        p = self.parser
        cfg = self.config
        pkg = cfg['package_base']
        block_const = camel_to_snake_upper(p.simple_name)
        be_const = block_const + '_BE'
        be_registry = p.be_registry_name
        #tick = self._tick_section()
        procedure = self._procedure_section()
        goggle = self._goggle_section()
        #tick_imports = self._get_tick_imports_str()

        # --- DEĞİŞEN KISIM ---
        mod_blocks_class = self._get_mod_blocks_class()
        # ---------------------

        goggle_import = ''
        if cfg.get('use_goggle_override'):
            goggle_import = (
                '\nimport com.simibubi.create.api.equipment.goggles.IHaveGoggleInformation;'
                '\nimport net.minecraft.network.chat.Component;'
                '\nimport java.util.List;'
            )

        goggle_implements = ', IHaveGoggleInformation' if cfg.get('use_goggle_override') else ''

        return f'''package {pkg}.block.entity;

import com.simibubi.create.api.stress.BlockStressValues;
import com.simibubi.create.content.kinetics.base.GeneratingKineticBlockEntity;{goggle_import}

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;

import {pkg}.init.{mod_blocks_class};
import {pkg}.init.{be_registry};

public class {p.block_entity_name} extends GeneratingKineticBlockEntity{goggle_implements} {{

    static {{
        BlockStressValues.CAPACITIES.registerProvider(
            block -> block == {mod_blocks_class}.{block_const}.get()
                ? () -> {cfg['stress_capacity']}
                : null
        );
    }}

    public {p.block_entity_name}(BlockEntityType<?> type, BlockPos pos, BlockState state) {{
        super(type != null ? type : {be_registry}.{be_const}.get(), pos, state);
    }}

    @Override
    public float getGeneratedSpeed() {{
        return {cfg['generated_speed']}f;
    }}

    @Override
    protected Block getStressConfigKey() {{
        return {mod_blocks_class}.{block_const}.get();
    }}

    @Override
    public void onLoad() {{
        super.onLoad();
        if (!level.isClientSide) {{
            updateGeneratedRotation();
        }}
    }}
{goggle}
}}
'''

    def _impact_entity(self):
        p = self.parser
        cfg = self.config
        pkg = cfg['package_base']
        block_const = camel_to_snake_upper(p.simple_name)
        be_const = block_const + '_BE'
        be_registry = p.be_registry_name
        #tick = self._tick_section()
        procedure = self._procedure_section()
        goggle = self._goggle_section()
        #tick_imports = self._get_tick_imports_str()

        # --- DEĞİŞEN KISIM ---
        mod_blocks_class = self._get_mod_blocks_class()
        # ---------------------

        goggle_import = ''
        if cfg.get('use_goggle_override'):
            goggle_import = (
                '\nimport com.simibubi.create.api.equipment.goggles.IHaveGoggleInformation;'
                '\nimport net.minecraft.network.chat.Component;'
                '\nimport java.util.List;'
            )
            
        procedure_import = ''
        if cfg.get('procedure'):
            procedure_import = (
                f'\nimport {pkg}.procedures.{cfg['procedure']}Procedure;'
            )

        goggle_implements = ', IHaveGoggleInformation' if cfg.get('use_goggle_override') else ''

        return f'''package {pkg}.block.entity;

import com.simibubi.create.content.kinetics.base.KineticBlockEntity;
import com.simibubi.create.foundation.blockEntity.behaviour.BlockEntityBehaviour;{goggle_import}

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;

import {pkg}.init.{mod_blocks_class};
import {pkg}.init.{be_registry};
{procedure_import}
import java.util.List;

public class {p.block_entity_name} extends KineticBlockEntity{goggle_implements} {{

    public {p.block_entity_name}(BlockEntityType<?> type, BlockPos pos, BlockState state) {{
        super(type != null ? type : {be_registry}.{be_const}.get(), pos, state);
    }}
    
    private int tickCounter = 0;
	private int tickTrigger = {cfg['tick_trigger']};
    private double minRpm = {cfg['rpm_threshold']};
    public double ImpactValue = {cfg['stress_impact']};
	
	public void setImpactValue(double value) {{
	    this.ImpactValue = value;
	    setChanged();
	}}

    @Override
    public void addBehaviours(List<BlockEntityBehaviour> behaviours) {{
        super.addBehaviours(behaviours);
    }}

    @Override
    public float calculateStressApplied() {{
        float impact = (float) ImpactValue;
        this.lastStressApplied = impact;
        return impact;
    }}

    @Override
    public void tick() {{
        super.tick();
        tickCounter++;
        if (tickCounter % tickTrigger == 0) {{
            if (minRpm >= Math.abs(this.getSpeed())) return;
            {procedure}
        }}
    }}
{goggle}
}}
'''