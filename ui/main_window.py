import customtkinter as ctk
import os
from tkinter import filedialog

from config import DEFAULT_CONFIG
from core.parser import JavaBlockParser
from core.transformer import BlockTransformer
from core.undo_manager import UndoManager
from generators.block_generator import BlockGenerator
from generators.entity_generator import EntityGenerator
from generators.registry_generator import RegistryGenerator

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Kinetic Block Converter")
        self.geometry("1200x700")
        #self.resizable(False, False)
        self.selected_path = None
        self.undo_manager = UndoManager()
        self._setup_ui()

    # ================================================================
    # UI KURULUM
    # ================================================================
    def _setup_ui(self):
        # Root container (horizontal split: left form + right log)
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=10, pady=10)

        # LEFT Panel (Form, Tabs, Buttons)
        left = ctk.CTkFrame(root, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Başlık (Left üzerinde)
        ctk.CTkLabel(
            left,
            text="⚙  Kinetic Block Converter",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(pady=(10, 2))

        ctk.CTkLabel(
            left,
            text="Block  →  DirectionalKineticBlock + IBE",
            text_color="gray",
            font=ctk.CTkFont(size=12)
        ).pack(pady=(0, 12))

        self._create_file_frame(left)
        self._create_tabs_and_controls(left)
        self._create_action_buttons(left)

        # RIGHT Panel (Log) - SABİT GENİŞLİK
        right = ctk.CTkFrame(root, width=700, fg_color="transparent")
        right.pack(side="right", fill="y", padx=(10, 0))
        right.pack_propagate(False)  # width'i 700 olarak sabit tutar (iç component sıkıştırmasın)

        self._create_log_frame(right)


    def _create_tabs_and_controls(self, parent):
        # Tab view - önceki setup’ten aynısını al; sadece parent parametresiyle paketleniyor
        self.tabview = ctk.CTkTabview(parent, height=370)
        self.tabview.pack(fill="x", padx=5, pady=8)

        self.tabview.add("Block Entity")
        self.tabview.add("Shaft")
        self.tabview.add("Renderer")
        self.tabview.add("Extras")
        self.tabview.add("Goggle") #todo

        self._create_entity_tab()
        self._create_shaft_tab()
        self._create_renderer_tab()
        self._create_extras_tab()
        self._create_goggle_tab() #todo


    def _create_action_buttons(self, parent):
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", padx=5, pady=(8, 3))

        ctk.CTkButton(
            btn_frame,
            text="⚙   CONVERT",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=48,
            command=self._convert
        ).pack(fill="x")

        self.undo_btn = ctk.CTkButton(
            btn_frame,
            text="↩  UNDO Last Convert",
            font=ctk.CTkFont(size=13),
            height=36,
            fg_color="gray30",
            hover_color="gray20",
            command=self._undo
        )
        # pack etmeyiz; convert sonrası göster


    def _create_file_frame(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(
            frame,
            text="Source File",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 4))

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=(0, 10))

        self.file_label = ctk.CTkLabel(
            inner,
            text="No file selected...",
            text_color="gray",
            anchor="w"
        )
        self.file_label.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            inner,
            text="📂 Browse",
            width=100,
            command=self._select_file
        ).pack(side="right")




    def _select_file(self):
        path = filedialog.askopenfilename(
            title="Select Block.java",
            filetypes=[("Java files", "*.java"), ("All files", "*.*")]
        )
        if path:
            self.selected_path = path
            self.file_label.configure(
                text=os.path.basename(path),
                text_color="white"
            )

    # ================================================================
    # BLOCK ENTITY TAB
    # ================================================================

    def _create_entity_tab(self):
        tab = self.tabview.tab("Block Entity")

        ctk.CTkLabel(
            tab,
            text="Entity Type",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=5, pady=(10, 5))

        self.type_var = ctk.StringVar(value="generator")
        type_row = ctk.CTkFrame(tab, fg_color="transparent")
        type_row.pack(anchor="w", padx=5)

        ctk.CTkRadioButton(
            type_row,
            text="⚡ Generator",
            variable=self.type_var,
            value="generator",
            command=self._toggle_entity_values
        ).pack(side="left", padx=(0, 20))

        ctk.CTkRadioButton(
            type_row,
            text="🔩 Impact",
            variable=self.type_var,
            value="impact",
            command=self._toggle_entity_values
        ).pack(side="left")

        self.values_container = ctk.CTkFrame(tab, fg_color="transparent")
        self.values_container.pack(fill="x", pady=(10, 0))

        self.gen_frame = ctk.CTkFrame(self.values_container, fg_color="transparent")
        self.capacity_entry = self._value_row(self.gen_frame, "Capacity", "16.0", "SU")
        self.speed_entry    = self._value_row(self.gen_frame, "Speed",    "64.0", "RPM")

        self.imp_frame = ctk.CTkFrame(self.values_container, fg_color="transparent")
        self.impact_entry = self._value_row(self.imp_frame, "Impact", "8.0", "SU")

        self._toggle_entity_values()

    def _value_row(self, parent, label, default, unit):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=3)
        ctk.CTkLabel(row, text=label, width=90, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(row, width=90)
        entry.insert(0, default)
        entry.pack(side="left", padx=5)
        ctk.CTkLabel(row, text=unit, text_color="gray").pack(side="left")
        return entry

    def _toggle_entity_values(self):
        self.gen_frame.pack_forget()
        self.imp_frame.pack_forget()
        if self.type_var.get() == "generator":
            self.gen_frame.pack(fill="x")
        else:
            self.imp_frame.pack(fill="x")

    # ================================================================
    # SHAFT TAB
    # ================================================================

    def _create_shaft_tab(self):
        tab = self.tabview.tab("Shaft")

        ctk.CTkLabel(tab, text="Shaft Faces",
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5, pady=(10, 3))

        ctk.CTkLabel(tab,
                    text="Select which faces the shaft connects to.\n"
                        "None = no shaft  |  All = always shaft",
                    text_color="gray", font=ctk.CTkFont(size=11),
                    justify="left").pack(anchor="w", padx=5, pady=(0, 8))

        self.shaft_vars = {}
        faces = [
            ("NORTH", "shaft_north"), ("SOUTH", "shaft_south"),
            ("EAST",  "shaft_east"),  ("WEST",  "shaft_west"),
            ("UP",    "shaft_up"),    ("DOWN",  "shaft_down"),
        ]
        grid = ctk.CTkFrame(tab, fg_color="transparent")
        grid.pack(anchor="w", padx=5)
        for idx, (label, key) in enumerate(faces):
            var = ctk.BooleanVar(value=False)
            self.shaft_vars[key] = var
            ctk.CTkCheckBox(grid, text=label, variable=var,
                        width=130).grid(row=idx//2, column=idx%2, padx=10, pady=5, sticky="w")

    # ================================================================
    # RENDERER TAB
    # ================================================================
    def _create_renderer_tab(self):
        tab = self.tabview.tab("Renderer")

        # Inner tabview - scroll'un DIŞINDA, direkt tab'a pack
        inner_tabview = ctk.CTkTabview(tab, height=300)
        inner_tabview.pack(fill="both", expand=True, padx=5, pady=5)

        inner_tabview.add("Shaft Renderer")
        inner_tabview.add("Cog Renderer")

        self._create_shaft_renderer_tab(inner_tabview.tab("Shaft Renderer"))
        self._create_cog_renderer_tab(inner_tabview.tab("Cog Renderer"))


    def _create_shaft_renderer_tab(self, parent):
        # Scroll burda - tab içeriği scroll'lanır ama tab başlıkları sabit kalır
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        self.render_shaft_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            scroll,
            text="Use Shaft Renderer",
            variable=self.render_shaft_var,
            command=lambda: self._toggle_inner_frame(
                self.render_shaft_var, self.shaft_renderer_frame
            )
        ).pack(anchor="w", padx=5, pady=(10, 5))

        self.shaft_renderer_frame = ctk.CTkFrame(scroll, fg_color="transparent")

        # Model
        ctk.CTkLabel(
            self.shaft_renderer_frame,
            text="Model:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=15, pady=(8, 3))

        self.shaft_model_var = ctk.StringVar(value="SHAFT")
        shaft_models = [
            ("SHAFT",          "SHAFT"),
            ("SHAFT_HALF",     "SHAFT_HALF"),
            ("COGWHEEL_SHAFT", "COGWHEEL_SHAFT"),
            ("POWERED_SHAFT",  "POWERED_SHAFT"),
            ("Custom (TODO)",  "CUSTOM"),
        ]
        model_grid = ctk.CTkFrame(self.shaft_renderer_frame, fg_color="transparent")
        model_grid.pack(anchor="w", padx=15)
        for i, (label, val) in enumerate(shaft_models):
            ctk.CTkRadioButton(
                model_grid,
                text=label,
                variable=self.shaft_model_var,
                value=val,
                width=150
            ).grid(row=i // 2, column=i % 2, padx=5, pady=2, sticky="w")

        # Placement
        ctk.CTkLabel(
            self.shaft_renderer_frame,
            text="Placement:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=15, pady=(10, 3))

        self.shaft_placement_var = ctk.StringVar(value="auto")
        placement_frame = ctk.CTkFrame(self.shaft_renderer_frame, fg_color="transparent")
        placement_frame.pack(anchor="w", padx=15)

        ctk.CTkRadioButton(
            placement_frame,
            text="Auto-detect (from Shaft Faces tab)",
            variable=self.shaft_placement_var,
            value="auto",
            command=self._toggle_shaft_placement
        ).pack(anchor="w", pady=2)

        ctk.CTkRadioButton(
            placement_frame,
            text="Manual Select",
            variable=self.shaft_placement_var,
            value="manual",
            command=self._toggle_shaft_placement
        ).pack(anchor="w", pady=2)

        self.shaft_manual_frame = ctk.CTkFrame(self.shaft_renderer_frame, fg_color="transparent")

        ctk.CTkLabel(
            self.shaft_manual_frame,
            text="Faces:",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(anchor="w", padx=20, pady=(5, 2))

        self.render_shaft_face_vars = {}
        manual_grid = ctk.CTkFrame(self.shaft_manual_frame, fg_color="transparent")
        manual_grid.pack(anchor="w", padx=20)
        for idx, (label, key) in enumerate([
            ("NORTH", "north"), ("SOUTH", "south"),
            ("EAST",  "east"),  ("WEST",  "west"),
            ("UP",    "up"),    ("DOWN",  "down"),
        ]):
            var = ctk.BooleanVar(value=False)
            self.render_shaft_face_vars[key] = var
            ctk.CTkCheckBox(
                manual_grid, text=label, variable=var, width=120
            ).grid(row=idx // 2, column=idx % 2, padx=5, pady=2, sticky="w")

        self.multiple_shafts_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self.shaft_manual_frame,
            text="Multiple Shafts (one per selected face)",
            variable=self.multiple_shafts_var
        ).pack(anchor="w", padx=15, pady=(8, 5))

        ctk.CTkLabel(
            self.shaft_renderer_frame,
            text="Rotation per Direction:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=15, pady=(12, 3))

        self.shaft_transform_entries = {}
        self._create_shaft_transform_grid(self.shaft_renderer_frame)

        self._toggle_shaft_placement()


    def _create_cog_renderer_tab(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        self.render_cog_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            scroll,
            text="Use Cog Renderer",
            variable=self.render_cog_var,
            command=lambda: self._toggle_inner_frame(
                self.render_cog_var, self.cog_renderer_frame
            )
        ).pack(anchor="w", padx=5, pady=(10, 5))

        self.cog_renderer_frame = ctk.CTkFrame(scroll, fg_color="transparent")

        ctk.CTkLabel(
            self.cog_renderer_frame,
            text="Model:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=15, pady=(8, 3))

        self.cog_model_var = ctk.StringVar(value="COGWHEEL")
        cog_models = [
            ("COGWHEEL",            "COGWHEEL"),
            ("SHAFTLESS_COGWHEEL",  "SHAFTLESS_COGWHEEL"),
            ("MILLSTONE_COG",       "MILLSTONE_COG"),
            ("MECHANICAL_PUMP_COG", "MECHANICAL_PUMP_COG"),
            ("ARM_COG",             "ARM_COG"),
            ("Custom (TODO)",       "CUSTOM"),
        ]
        cog_model_frame = ctk.CTkFrame(self.cog_renderer_frame, fg_color="transparent")
        cog_model_frame.pack(anchor="w", padx=15)
        for label, val in cog_models:
            ctk.CTkRadioButton(
                cog_model_frame,
                text=label,
                variable=self.cog_model_var,
                value=val
            ).pack(anchor="w", pady=2)

        ctk.CTkLabel(
            self.cog_renderer_frame,
            text="Transform per Facing:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=15, pady=(12, 3))

        self.cog_transform_entries = {}
        self._create_cog_transform_grid(self.cog_renderer_frame)


    # Tek bir toggle helper - ikisi için ortak
    def _toggle_inner_frame(self, var, frame):
        if var.get():
            frame.pack(anchor="w", fill="x", padx=5, pady=5)
        else:
            frame.pack_forget()


    def _toggle_shaft_placement(self):
        if self.shaft_placement_var.get() == "manual":
            self.shaft_manual_frame.pack(anchor="w", fill="x", pady=5)
        else:
            self.shaft_manual_frame.pack_forget()

    def _create_shaft_transform_grid(self, parent):
        from config import DEFAULT_CONFIG
        defaults = DEFAULT_CONFIG.get("shaft_transform", {})

        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(0, 3))
        for col, text in enumerate(["Dir", "Rot X", "Rot Y", "Rot Z"]):
            ctk.CTkLabel(
                header,
                text=text,
                width=65,
                font=ctk.CTkFont(size=11),
                text_color="gray"
            ).grid(row=0, column=col, padx=2)

        for d in ["NORTH", "SOUTH", "EAST", "WEST", "UP", "DOWN"]:
            row_frame = ctk.CTkFrame(parent, fg_color="transparent")
            row_frame.pack(fill="x", padx=15, pady=2)

            ctk.CTkLabel(
                row_frame,
                text=d,
                width=65,
                font=ctk.CTkFont(size=11)
            ).grid(row=0, column=0, padx=2)

            t = defaults.get(d, {})
            entries = {}
            for col, (key, default) in enumerate([
                ("rotate_x", t.get("rotate_x", 0.0)),
                ("rotate_y", t.get("rotate_y", 0.0)),
                ("rotate_z", t.get("rotate_z", 0.0)),
            ]):
                entry = ctk.CTkEntry(row_frame, width=65)
                entry.insert(0, str(default))
                entry.grid(row=0, column=col + 1, padx=2)
                entries[key] = entry

            self.shaft_transform_entries[d] = entries


    def _create_cog_transform_grid(self, parent):
        from config import DEFAULT_CONFIG
        defaults = DEFAULT_CONFIG.get("cog_transform", {})

        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(0, 3))
        for col, text in enumerate(["Facing", "Rot X", "Rot Y", "Rot Z", "Off X", "Off Y", "Off Z"]):
            ctk.CTkLabel(
                header,
                text=text,
                width=60,
                font=ctk.CTkFont(size=11),
                text_color="gray"
            ).grid(row=0, column=col, padx=2)

        for d in ["NORTH", "SOUTH", "EAST", "WEST", "UP", "DOWN"]:
            row_frame = ctk.CTkFrame(parent, fg_color="transparent")
            row_frame.pack(fill="x", padx=15, pady=2)

            ctk.CTkLabel(
                row_frame,
                text=d,
                width=60,
                font=ctk.CTkFont(size=11)
            ).grid(row=0, column=0, padx=2)

            t = defaults.get(d, {})
            entries = {}
            for col, (key, default) in enumerate([
                ("rotate_x", t.get("rotate_x", 0.0)),
                ("rotate_y", t.get("rotate_y", 0.0)),
                ("rotate_z", t.get("rotate_z", 0.0)),
                ("offset_x", t.get("offset_x", 0.0)),
                ("offset_y", t.get("offset_y", 0.0)),
                ("offset_z", t.get("offset_z", 0.0)),
            ]):
                entry = ctk.CTkEntry(row_frame, width=55)
                entry.insert(0, str(default))
                entry.grid(row=0, column=col + 1, padx=2)
                entries[key] = entry

            self.cog_transform_entries[d] = entries
    # ================================================================
    # EXTRAS TAB
    # ================================================================

    def _create_extras_tab(self):
        tab = self.tabview.tab("Extras")

        ctk.CTkLabel(
            tab,
            text="Interfaces",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=5, pady=(10, 8))

        # ICogWheel - sadece checkbox, radio yok
        self.cogwheel_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            tab,
            text="ICogWheel",
            variable=self.cogwheel_var,
        ).pack(anchor="w", padx=5, pady=(0, 5))

        ctk.CTkLabel(
            tab,
            text="Adds cogwheel interaction to the block.",
            text_color="gray",
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=25)

    def _toggle_cogwheel(self):
        if self.cogwheel_var.get():
            self.cog_size_frame.pack(anchor="w", pady=(0, 5))
        else:
            self.cog_size_frame.pack_forget()

    # ================================================================
    # GOGGLE TAB
    # ================================================================

    def _create_goggle_tab(self):
        tab = self.tabview.tab("Goggle")

        ctk.CTkLabel(
            tab,
            text="Goggle Information",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=5, pady=(10, 5))

        self.goggle_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            tab,
            text="Override addToGoggleTooltip",
            variable=self.goggle_var,
            command=self._toggle_goggle
        ).pack(anchor="w", padx=5, pady=(0, 5))

        self.goggle_info = ctk.CTkLabel(
            tab,
            text="ℹ  Implements IHaveGoggleInformation on both\n"
                 "   Block and Block Entity with a TODO stub.",
            text_color="#4a9eff",
            font=ctk.CTkFont(size=11),
            justify="left"
        )

    def _toggle_goggle(self):
        if self.goggle_var.get():
            self.goggle_info.pack(anchor="w", padx=5)
        else:
            self.goggle_info.pack_forget()
    # ================================================================
    # HELPERS
    # ================================================================

    def _mod_id_to_pascal(self, mod_id: str) -> str:
        if '_' in mod_id:
            return ''.join(part.capitalize() for part in mod_id.split('_'))
        else:
            return mod_id.capitalize()

    def _get_mod_class(self, cfg: dict) -> str:
        mod_id = cfg.get('mod_id', 'createplugintest')
        return f"{self._mod_id_to_pascal(mod_id)}Mod"
    
    # ================================================================
    # LOG
    # ================================================================

    def _create_log_frame(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="both", expand=True, padx=0, pady=0)

        ctk.CTkLabel(
            frame,
            text="Log",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 4))

        self.log_text = ctk.CTkTextbox(
            frame,
            font=ctk.CTkFont(family="Courier", size=12),
            state="disabled"
        )
        self.log_text.pack(fill="both", expand=True, padx=15, pady=(0, 5))

        # Clear Log butonu en altta
        ctk.CTkButton(
            frame,
            text="🗑️  Clear Log",
            font=ctk.CTkFont(size=12),
            height=28,
            fg_color="gray30",
            hover_color="gray20",
            command=self._clear_log
        ).pack(fill="x", padx=15, pady=(0, 10))

    def _log(self, msg):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.configure(state="disabled")
        self.log_text.see("end")

    def _clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    # ================================================================
    # CONFIG
    # ================================================================

    def _get_config(self):
        cfg = DEFAULT_CONFIG.copy()
        cfg.update({
            'is_generator':        self.type_var.get() == 'generator',
            'use_cogwheel':        self.cogwheel_var.get(),
            'use_goggle_override': False, #self.goggle_var.get(),
            'render_shaft':        self.render_shaft_var.get(),
            'shaft_model':         self.shaft_model_var.get(),
            'shaft_placement':     self.shaft_placement_var.get(),
            'multiple_shafts':     self.multiple_shafts_var.get(),
            'render_cog':          self.render_cog_var.get(),
            'cog_model':           self.cog_model_var.get(),
        })

        # Shaft faces (direction bazlı)
        for key, var in self.shaft_vars.items():
            cfg[key] = var.get()  # shaft_north, shaft_south vs.
        
        # Shaft transform
        shaft_transform = {}
        for d, entries in self.shaft_transform_entries.items():
            t = {}
            for key, entry in entries.items():
                try:
                    t[key] = float(entry.get())
                except ValueError:
                    t[key] = 0.0
            shaft_transform[d] = t
        cfg['shaft_transform'] = shaft_transform

        # Renderer shaft manual faces
        for key, var in self.render_shaft_face_vars.items():
            cfg[f"render_shaft_{key}"] = var.get()
        # Renderer shaft manual faces
        for key, var in self.render_shaft_face_vars.items():
            cfg[f"render_shaft_{key}"] = var.get()

        # Cog transform
        cog_transform = {}
        for d, entries in self.cog_transform_entries.items():
            t = {}
            for key, entry in entries.items():
                try:
                    t[key] = float(entry.get())
                except ValueError:
                    t[key] = 0.0
            cog_transform[d] = t
        cfg['cog_transform'] = cog_transform

        try:
            cfg['stress_capacity'] = float(self.capacity_entry.get())
        except ValueError:
            cfg['stress_capacity'] = 16.0
        try:
            cfg['generated_speed'] = float(self.speed_entry.get())
        except ValueError:
            cfg['generated_speed'] = 64.0
        try:
            cfg['stress_impact'] = float(self.impact_entry.get())
        except ValueError:
            cfg['stress_impact'] = 8.0

        return cfg

    # ================================================================
    # CONVERT
    # ================================================================

    def _convert(self):
        #self._clear_log()

        if not self.selected_path:
            self._log("❌  No file selected!")
            return

        # Eğer undo varsa önce undo yap
        if self.undo_manager.has_undo:
            self._log("↩️  Auto-undoing previous convert...")
            log = self.undo_manager.undo()
            for line in log:
                self._log(line)
            self._log("")
            self.undo_btn.pack_forget()

        try:
            with open(self.selected_path, 'r', encoding='utf-8') as f:
                content = f.read()

            block_name = os.path.basename(self.selected_path).replace('.java', '')
            cfg = self._get_config()

            self._log(f"📄  Reading: {block_name}.java")
            self._log("")

            parser      = JavaBlockParser(content, block_name)
            transformer = BlockTransformer(parser, cfg)

            block_gen  = BlockGenerator(transformer, self.selected_path)
            block_path = block_gen.generate(self.undo_manager)
            self._log(f"✅  Block:    {os.path.basename(block_path)}")

            entity_gen  = EntityGenerator(transformer, cfg, self.selected_path)
            entity_path = entity_gen.generate(self.undo_manager)
            self._log(f"✅  Entity:   {os.path.basename(entity_path)}")

            registry_gen  = RegistryGenerator(parser, cfg, self.selected_path)
            registry_path = registry_gen.generate(self.undo_manager)
            self._log(f"✅  Registry: {os.path.basename(registry_path)}")

            if cfg.get("render_shaft") or cfg.get("render_cog"):
                from generators.client_generator import ClientGenerator
                client_gen = ClientGenerator(parser, cfg, self.selected_path)
                renderer_path, handler_path = client_gen.generate(self.undo_manager)
                self._log(f"✅  Renderer: {os.path.basename(renderer_path)}")
                self._log(f"✅  Client:   {os.path.basename(handler_path)}")

            for w in transformer.warnings:
                self._log(w)

            if transformer.tick_body:
                self._log("ℹ️   tick() moved to block entity")

            self._log("")
            self._log("🎉  Done!")
            self._log("")
            self._log(f"📋  Add to {self._get_mod_class(cfg)}.java:")
            self._log(f"    {parser.be_registry_name}.register(modEventBus);")
            self._log("")
            self.undo_manager.has_undo = True
            self.undo_btn.pack(fill="x", pady=(5, 0))

        except Exception as e:
            self._log(f"❌  Error: {str(e)}")
            import traceback
            self._log(traceback.format_exc())

    # ================================================================
    # UNDO
    # ================================================================

    def _undo(self):
        #self._clear_log()
        self._log("↩️  Undoing last convert...")
        self._log("")
        log = self.undo_manager.undo()
        for line in log:
            self._log(line)
        self._log("")
        self._log("✅  Undo complete!")
        self._log("")
        self.undo_btn.pack_forget()