import os
import re
from config import DEFAULT_CONFIG

SHAFT_MODELS = {
    "SHAFT":          "AllPartialModels.SHAFT",
    "SHAFT_HALF":     "AllPartialModels.SHAFT_HALF",
    "COGWHEEL_SHAFT": "AllPartialModels.COGWHEEL_SHAFT",
    "POWERED_SHAFT":  "AllPartialModels.POWERED_SHAFT",
    "CUSTOM":         "null /* TODO: custom partial model */",
}

COG_MODELS = {
    "COGWHEEL":            "AllPartialModels.COGWHEEL",
    "SHAFTLESS_COGWHEEL":  "AllPartialModels.SHAFTLESS_COGWHEEL",
    "MILLSTONE_COG":       "AllPartialModels.MILLSTONE_COG",
    "MECHANICAL_PUMP_COG": "AllPartialModels.MECHANICAL_PUMP_COG",
    "ARM_COG":             "AllPartialModels.ARM_COG",
    "CUSTOM":              "null /* TODO: custom partial model */",
}

# Direction → Axis mapping
DIRECTION_AXIS = {
    "NORTH": "Axis.Z",
    "SOUTH": "Axis.Z",
    "EAST":  "Axis.X",
    "WEST":  "Axis.X",
    "UP":    "Axis.Y",
    "DOWN":  "Axis.Y",
}

ALL_DIRECTIONS = ["NORTH", "SOUTH", "EAST", "WEST", "UP", "DOWN"]


class ClientGenerator:
    def __init__(self, parser, config, input_path):
        self.parser = parser
        self.config = config
        self.input_path = input_path

    def generate(self, undo_manager=None):
        block_dir = os.path.dirname(self.input_path)
        parent_dir = os.path.dirname(block_dir)
        client_dir = os.path.join(
            parent_dir, self.config.get("path_client_dir", "client")
        )
        os.makedirs(client_dir, exist_ok=True)

        renderer_content = self._build_renderer()
        renderer_name = self.parser.simple_name + "Renderer"
        renderer_path = os.path.join(client_dir, f"{renderer_name}.java")
        with open(renderer_path, 'w', encoding='utf-8') as f:
            f.write(renderer_content)

        handler_content = self._build_handler()
        handler_name = self.parser.simple_name + "ClientHandler"
        handler_path = os.path.join(client_dir, f"{handler_name}.java")
        with open(handler_path, 'w', encoding='utf-8') as f:
            f.write(handler_content)

        if undo_manager:
            undo_manager.track_created(renderer_path)
            undo_manager.track_created(handler_path)

        return renderer_path, handler_path

    # ================================================================
    # RENDERER BUILD
    # ================================================================

    def _build_renderer(self):
        p = self.parser
        cfg = self.config
        pkg = cfg["package_base"]
        renderer_name = p.simple_name + "Renderer"
        be_name = p.block_entity_name

        render_shaft = cfg.get("render_shaft", False)
        render_cog = cfg.get("render_cog", False)
        multiple = cfg.get("multiple_shafts", False)

        shaft_faces = self._get_shaft_faces()
        shaft_model = SHAFT_MODELS.get(cfg.get("shaft_model", "SHAFT"), "AllPartialModels.SHAFT")
        cog_model = COG_MODELS.get(cfg.get("cog_model", "COGWHEEL"), "AllPartialModels.COGWHEEL")

        # Artık her zaman renderSafe kullanıyoruz, getRotatedModel yok
        imports = self._build_renderer_imports(pkg)
        render_method = self._build_render_method(
            render_shaft, render_cog, multiple,
            shaft_faces, shaft_model, cog_model, be_name
        )

        return f'''package {pkg}.client;

{imports}

public class {renderer_name} extends KineticBlockEntityRenderer<{be_name}> {{

    public {renderer_name}(BlockEntityRendererProvider.Context context) {{
        super(context);
    }}

{render_method}
}}
'''

    def _build_renderer_imports(self, pkg):
        lines = [
            "import com.simibubi.create.AllPartialModels;",
            "import com.simibubi.create.content.kinetics.base.KineticBlockEntityRenderer;",
            "",
            "import dev.engine_room.flywheel.lib.model.baked.PartialModel;",
            "import net.createmod.catnip.render.CachedBuffers;",
            "import net.createmod.catnip.render.SuperByteBuffer;",
            "",
            "import com.mojang.blaze3d.vertex.PoseStack;",
            "import net.minecraft.client.renderer.MultiBufferSource;",
            "import net.minecraft.client.renderer.RenderType;",
            "import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;",
            "import net.minecraft.core.Direction;",
            "import net.minecraft.core.Direction.Axis;",
            "import net.minecraft.world.level.block.state.BlockState;",
            "import net.createmod.catnip.animation.AnimationTickHolder;",
            "import net.minecraft.core.BlockPos;",
            "",
            f"import {pkg}.block.entity.{self.parser.block_entity_name};",
            f"import {pkg}.init.{self.parser.be_registry_name};",
        ]

        return "\n".join(lines)

    # ================================================================
    # RENDER METHOD
    # ================================================================

    def _build_render_method(self, render_shaft, render_cog, multiple,
                             shaft_faces, shaft_model, cog_model, be_name):
        # Her zaman renderSafe kullan
        return self._build_render_safe(
            render_shaft, render_cog, multiple,
            shaft_faces, shaft_model, cog_model, be_name
        )

    # ================================================================
    # RENDER SAFE
    # ================================================================

    def _build_render_safe(self, render_shaft, render_cog, multiple,
                           shaft_faces, shaft_model, cog_model, be_name):

        render_calls = []

        # SHAFT
        if render_shaft:
            face_list = shaft_faces if (multiple or len(shaft_faces) > 1) else [shaft_faces[0]]
            for face in face_list:
                axis = DIRECTION_AXIS.get(face, "Axis.Z")

                t = self.config.get("shaft_transform", {}).get(face, {})
                rx = t.get("rotate_x", 0.0)
                ry = t.get("rotate_y", 0.0)
                rz = t.get("rotate_z", 0.0)
                has_extra = rx != 0.0 or ry != 0.0 or rz != 0.0

                extra_transform = ""
                if has_extra:
                    extra_transform += "            shaftBuf.translate(0.5f, 0.5f, 0.5f);\n"
                    if rx != 0.0:
                        extra_transform += f"            shaftBuf.rotateX((float) Math.toRadians({rx}));\n"
                    if ry != 0.0:
                        extra_transform += f"            shaftBuf.rotateY((float) Math.toRadians({ry}));\n"
                    if rz != 0.0:
                        extra_transform += f"            shaftBuf.rotateZ((float) Math.toRadians({rz}));\n"
                    extra_transform += "            shaftBuf.translate(-0.5f, -0.5f, -0.5f);\n"

                render_calls.append(
                    f"        // shaft - {face}\n"
                    f"        {{\n"
                    f"            SuperByteBuffer shaftBuf = CachedBuffers.partialFacing(\n"
                    f"                {shaft_model}, state, Direction.{face});\n"
                    f"            float offset = getRotationOffsetForPosition(be, be.getBlockPos(), {axis});\n"
                    f"            float time = AnimationTickHolder.getRenderTime(be.getLevel());\n"
                    f"            float angle = ((time * be.getSpeed() * 3f / 10 + offset) % 360) / 180f * (float) Math.PI;\n"
                    f"{extra_transform}"
                    f"            kineticRotationTransform(shaftBuf, be, {axis}, angle, light);\n"
                    f"            shaftBuf.renderInto(ms, buffer.getBuffer(type));\n"
                    f"        }}"
                )

        # COG
        if render_cog:
            cog_switch = self._build_cog_transform_switch()
            has_transform = bool(cog_switch.strip())

            if has_transform:
                render_calls.append(
                    f"        // cog\n"
                    f"        {{\n"
                    f"            SuperByteBuffer cogBuf = CachedBuffers.partial({cog_model}, state);\n"
                    f"            KineticBlockEntityRenderer.standardKineticRotationTransform(cogBuf, be, light);\n"
                    f"{cog_switch}"
                    f"            cogBuf.renderInto(ms, buffer.getBuffer(type));\n"
                    f"        }}"
                )
            else:
                render_calls.append(
                    f"        // cog\n"
                    f"        {{\n"
                    f"            SuperByteBuffer cogBuf = CachedBuffers.partial({cog_model}, state);\n"
                    f"            KineticBlockEntityRenderer.renderRotatingBuffer(be, cogBuf, ms, buffer.getBuffer(type), light);\n"
                    f"        }}"
                )

        render_body = "\n\n".join(render_calls)

        return (
            f"    @Override\n"
            f"    protected void renderSafe({be_name} be, float partialTicks, PoseStack ms,\n"
            f"            MultiBufferSource buffer, int light, int overlay) {{\n"
            f"\n"
            f"        BlockState state = be.getBlockState();\n"
            f"        RenderType type = getRenderType(be, state);\n"
            f"\n"
            f"{render_body}\n"
            f"    }}\n"
        )

    # ================================================================
    # COG TRANSFORM
    # ================================================================

    def _build_cog_transform_switch(self):
        transforms = self.config.get("cog_transform", {})

        has_any = any(
            any(v != 0.0 for v in t.values())
            for t in transforms.values()
        )
        if not has_any:
            return ""

        lines = (
            f"            Direction facing = state.getValue(\n"
            f"                com.simibubi.create.content.kinetics.base.DirectionalKineticBlock.FACING);\n"
            f"            switch (facing) {{\n"
        )

        for d in ALL_DIRECTIONS:
            t = transforms.get(d, {})
            rx = t.get("rotate_x", 0.0)
            ry = t.get("rotate_y", 0.0)
            rz = t.get("rotate_z", 0.0)
            ox = t.get("offset_x", 0.0)
            oy = t.get("offset_y", 0.0)
            oz = t.get("offset_z", 0.0)

            body = ""
            has_rotation = rx != 0.0 or ry != 0.0 or rz != 0.0
            if has_rotation:
                body += f"                cogBuf.translate(0.5f, 0.5f, 0.5f);\n"
                if rx != 0.0:
                    body += f"                cogBuf.rotateX((float) Math.toRadians({rx}));\n"
                if ry != 0.0:
                    body += f"                cogBuf.rotateY((float) Math.toRadians({ry}));\n"
                if rz != 0.0:
                    body += f"                cogBuf.rotateZ((float) Math.toRadians({rz}));\n"
                body += f"                cogBuf.translate(-0.5f, -0.5f, -0.5f);\n"

            if ox != 0.0 or oy != 0.0 or oz != 0.0:
                body += f"                cogBuf.translate({ox}f, {oy}f, {oz}f);\n"

            if body:
                lines += f"                case {d} -> {{\n{body}                }}\n"
            else:
                lines += f"                case {d} -> {{}}\n"

        lines += "            }\n"
        return lines

    # ================================================================
    # SHAFT FACES
    # ================================================================

    def _get_shaft_faces(self):
        cfg = self.config
        placement = cfg.get("shaft_placement", "auto")

        if placement == "auto":
            faces = [
                d for d in ALL_DIRECTIONS
                if cfg.get(f"shaft_{d.lower()}", False)
            ]
            return faces if faces else ["NORTH"]
        else:
            faces = [
                d for d in ALL_DIRECTIONS
                if cfg.get(f"render_shaft_{d.lower()}", False)
            ]
            return faces if faces else ["NORTH"]

    # ================================================================
    # HANDLER
    # ================================================================

    def _build_handler(self):
        p = self.parser
        cfg = self.config
        pkg = cfg["package_base"]
        handler_name = p.simple_name + "ClientHandler"
        renderer_name = p.simple_name + "Renderer"
        be_registry = p.be_registry_name
        block_const = _camel_to_snake_upper(p.simple_name)
        be_const = block_const + "_BE"

        return f'''package {pkg}.client;

import net.neoforged.bus.api.IEventBus;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.event.lifecycle.FMLClientSetupEvent;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderers;

import {pkg}.init.{be_registry};

public class {handler_name} {{

    public static void register(IEventBus modEventBus) {{
        modEventBus.addListener({handler_name}::onClientSetup);
    }}

    @SubscribeEvent
    public static void onClientSetup(FMLClientSetupEvent event) {{
        event.enqueueWork(() -> {{
            BlockEntityRenderers.register(
                {be_registry}.{be_const}.get(),
                {renderer_name}::new
            );
        }});
    }}
}}
'''


def _camel_to_snake_upper(name):
    s = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    s = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s)
    return s.upper()