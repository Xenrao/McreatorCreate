import re

def camel_to_snake_upper(name):
    s = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    s = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s)
    return s.upper()


class BlockTransformer:
    REMOVE_METHODS = {'rotate', 'mirror'}
    EXTRACT_METHODS = {'tick'}
    REMOVE_IMPORTS = {
        'import net.minecraft.world.level.block.DirectionalBlock;',
        'import net.minecraft.world.level.block.HorizontalDirectionalBlock;',
        'import net.minecraft.world.level.block.state.properties.DirectionProperty;',
        'import net.minecraft.world.level.block.Rotation;',
        'import net.minecraft.world.level.block.Mirror;',
        'import net.minecraft.world.level.block.RotatedPillarBlock;',
        'import net.minecraft.world.level.block.*;',
        'import net.minecraft.server.level.ServerLevel;',
    }
    WILDCARD_REPLACEMENTS = [
        'import net.minecraft.world.level.block.Block;',
        'import net.minecraft.world.level.block.SoundType;',
    ]

    def __init__(self, parser, config):
        self.parser = parser
        self.config = config
        self.tick_body = None
        self.tick_imports = []  # BU SATIRI EKLE
        self.warnings = []

    def transform(self):
        package = self.parser.get_package()
        imports = self._build_imports()
        class_body = self._transform_body()
        implements = self._build_implements()

        lines = [package, '']
        lines.extend(imports)
        lines.append('')
        lines.append(
            f'public class {self.parser.block_name} '
            f'extends DirectionalKineticBlock implements {implements} {{'
        )
        lines.append(class_body)
        lines.append('}')
        lines.append('')
        return '\n'.join(lines)

    def _build_imports(self):
        existing = self.parser.get_imports()
        final = []

        for imp in existing:
            if imp in self.REMOVE_IMPORTS:
                continue
            if imp == 'import net.minecraft.world.level.block.*;':
                final.extend(self.WILDCARD_REPLACEMENTS)
                continue
            final.append(imp)

        add = [
            'import com.simibubi.create.content.kinetics.base.DirectionalKineticBlock;',
            'import com.simibubi.create.foundation.block.IBE;',
            'import net.minecraft.world.level.LevelReader;',
            'import net.minecraft.world.level.Level;',
            'import net.minecraft.core.BlockPos;',
            'import net.minecraft.world.level.block.entity.BlockEntityType;',
            f'import {self.config["package_base"]}.block.entity.{self.parser.block_entity_name};',
            f'import {self.config["package_base"]}.init.{self.parser.be_registry_name};',
        ]

        if self.config.get('use_cogwheel'):
            add.append('import com.simibubi.create.content.kinetics.simpleRelays.ICogWheel;')

        if self.parser.has_simple_waterlogged():
            add.extend([
                'import net.minecraft.world.level.block.SimpleWaterloggedBlock;',
                'import net.minecraft.world.level.material.Fluids;',
                'import net.minecraft.world.level.material.FluidState;',
                'import net.minecraft.world.level.LevelAccessor;',
            ])

        # Goggle import
        if self.config.get('use_goggle_override'):
            add.extend([
                'import com.simibubi.create.api.equipment.goggles.IHaveGoggleInformation;',
                'import net.minecraft.network.chat.Component;',
                'import net.minecraft.world.entity.player.Player;',
                'import net.minecraft.world.level.Level;',
                'import java.util.List;',
            ])

        for imp in add:
            if imp not in final:
                final.append(imp)

        return self._sort_imports(final)

    def _sort_imports(self, imports):
        imports = list(dict.fromkeys(imports))
        groups = [
            sorted(i for i in imports if 'com.simibubi' in i),
            sorted(i for i in imports if i.startswith('import com.') and 'simibubi' not in i),
            sorted(i for i in imports if 'net.neoforged' in i),
            sorted(i for i in imports if 'net.minecraft' in i),
            sorted(i for i in imports if 'net.mcreator' in i),
            sorted(i for i in imports if i.startswith('import java')),
        ]
        result = []
        for g in groups:
            if g:
                result.extend(g)
                result.append('')
        if result and result[-1] == '':
            result.pop()
        return result

    def _transform_body(self):
        body = self.parser.get_class_body()
        body = re.sub(r'[ \t]*public static final DirectionProperty FACING = .*?;\n', '', body)

        if self.parser.has_axis():
            self.warnings.append("⚠️  AXIS usage detected, please review!")

        body, self.tick_body = self._process_methods(body)
        body = self._fix_state_definition(body)
        body = self._inject_new_methods(body)
        return body
    
    def _collect_tick_imports(self, tick_lines):
        imports = []
        pkg = self.config['package_base']
        for line in tick_lines:
            matches = re.findall(r'\b([A-Z]\w+Procedure)\b', line)
            for cls in matches:
                imp = f'import {pkg}.procedures.{cls};'
                if imp not in imports:
                    imports.append(imp)
        return imports

    def _process_methods(self, body):
        lines = body.split('\n')
        result = []
        tick_body = None
        i = 0
        while i < len(lines):
            method_name = self.parser._detect_method_name(lines, i)
            if method_name:
                method_block, end_i = self.parser._extract_method_block(lines, i)
                if method_name in self.REMOVE_METHODS:
                    i = end_i + 1
                    continue
                elif method_name in self.EXTRACT_METHODS:
                    tick_body = self.parser.get_tick_body(method_block)
                    self.tick_imports = self._collect_tick_imports(tick_body)
                    result.append("    // TODO: tick() moved to block entity")
                    result.append('')
                    i = end_i + 1
                    continue
                else:
                    result.extend(method_block)
                    i = end_i + 1
                    continue
            result.append(lines[i])
            i += 1
        return '\n'.join(result), tick_body

    def _fix_state_definition(self, body):
        def replacer(match):
            override = match.group(1) or ''
            inner = match.group(2)
            add_match = re.search(r'builder\.add\(([^)]*)\);', inner)
            if add_match:
                args_raw = add_match.group(1).strip()
                args_list = [
                    a.strip() for a in args_raw.split(',')
                    if a.strip() and a.strip() != 'FACING'
                ]
                if args_list:
                    new_args = ', '.join(args_list)
                    return (
                        f'{override}protected void createBlockStateDefinition('
                        f'StateDefinition.Builder<Block, BlockState> builder) {{\n'
                        f'        builder.add({new_args});\n'
                        f'        super.createBlockStateDefinition(builder);\n'
                        f'    }}'
                    )
                else:
                    return (
                        f'{override}protected void createBlockStateDefinition('
                        f'StateDefinition.Builder<Block, BlockState> builder) {{\n'
                        f'        super.createBlockStateDefinition(builder);\n'
                        f'    }}'
                    )
            return match.group(0)

        pattern = (
            r'(@Override\s+)?protected void createBlockStateDefinition'
            r'\(StateDefinition\.Builder<Block, BlockState> builder\) \{([^}]+)\}'
        )
        return re.sub(pattern, replacer, body, flags=re.DOTALL)

    def _inject_new_methods(self, body):
        ibe = self._gen_ibe_methods()
        kinetic = self._gen_kinetic_methods()
        on_remove = self._gen_on_remove()
        goggle = self._gen_goggle_method() if self.config.get('use_goggle_override') else ''

        constructor_end = self._find_constructor_end(body)
        if constructor_end == -1:
            return body

        insert = '\n' + ibe + '\n' + kinetic + '\n' + on_remove
        if goggle:
            insert += '\n' + goggle

        return body[:constructor_end] + insert + body[constructor_end:]

    def _gen_ibe_methods(self):
        be_name = self.parser.block_entity_name
        be_registry = camel_to_snake_upper(self.parser.simple_name) + '_BE'
        registry_class = self.parser.be_registry_name
        return (
            f'    // ---- IBE ----\n'
            f'    @Override\n'
            f'    public Class<{be_name}> getBlockEntityClass() {{\n'
            f'        return {be_name}.class;\n'
            f'    }}\n\n'
            f'    @Override\n'
            f'    public BlockEntityType<? extends {be_name}> getBlockEntityType() {{\n'
            f'        return {registry_class}.{be_registry}.get();\n'
            f'    }}\n'
        )

    def _gen_kinetic_methods(self):
        shaft_condition = self._build_shaft_condition()
        return (
            '    // ---- KINETIC ----\n'
            '    @Override\n'
            '    public boolean hasShaftTowards(LevelReader world, BlockPos pos, BlockState state, Direction face) {\n'
            f'        {shaft_condition}\n'
            '    }\n\n'
            '    @Override\n'
            '    public Direction.Axis getRotationAxis(BlockState state) {\n'
            '        return state.getValue(FACING).getAxis();\n'
            '    }\n'
        )

    def _build_shaft_condition(self):
        cfg = self.config
        checks = []

        if cfg.get('shaft_north'): checks.append('face == Direction.NORTH')
        if cfg.get('shaft_south'): checks.append('face == Direction.SOUTH')
        if cfg.get('shaft_east'):  checks.append('face == Direction.EAST')
        if cfg.get('shaft_west'):  checks.append('face == Direction.WEST')
        if cfg.get('shaft_up'):    checks.append('face == Direction.UP')
        if cfg.get('shaft_down'):  checks.append('face == Direction.DOWN')

        if not checks:
            return 'return false;'
        if len(checks) == 6:
            return 'return true;'

        condition = ' || '.join(checks)
        return f'return {condition};'

    def _gen_on_remove(self):
        return (
            '    @Override\n'
            '    public void onRemove(BlockState state, Level world, BlockPos pos,'
            ' BlockState newState, boolean isMoving) {\n'
            '        super.onRemove(state, world, pos, newState, isMoving);\n'
            '    }\n'
        )

    def _gen_goggle_method(self):
        return (
            '    // ---- GOGGLE ----\n'
            '    @Override\n'
            '    public boolean addToGoggleTooltip(List<Component> tooltip, boolean isPlayerSneaking) {\n'
            '        // TODO: Add goggle tooltip content\n'
            '        return super.addToGoggleTooltip(tooltip, isPlayerSneaking);\n'
            '    }\n'
        )

    def _build_implements(self):
        parts = [f'IBE<{self.parser.block_entity_name}>']
        if self.parser.has_simple_waterlogged():
            parts.append('SimpleWaterloggedBlock')
        if self.config.get('use_cogwheel'):
            parts.append('ICogWheel')
        if self.config.get('use_goggle_override'):
            parts.append('IHaveGoggleInformation')
        return ', '.join(parts)

    def _find_constructor_end(self, body):
        match = re.search(rf'public {self.parser.block_name}\s*\(', body)
        if not match:
            return -1
        start = match.start()
        brace_count = 0
        found_open = False
        for i in range(start, len(body)):
            if body[i] == '{':
                brace_count += 1
                found_open = True
            elif body[i] == '}':
                brace_count -= 1
            if found_open and brace_count == 0:
                return i + 1
        return -1