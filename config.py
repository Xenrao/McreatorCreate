import json
import os
import sys

def get_config_path():
    if getattr(sys, 'frozen', False):
        base_path = os.getenv("APPDATA") 
        app_folder = os.path.join(base_path, "KineticBlockConverter") 
        os.makedirs(app_folder, exist_ok=True)
        return os.path.join(app_folder, "user_config.json")
    else:
        return os.path.join(os.path.dirname(__file__), "user_config.json")

CONFIG_SAVE_PATH = get_config_path()


DEFAULT_CONFIG = {
    "mod_id": "",
    "package_base": "",
    "path_block_dir": "block",
    "path_entity_dir": "block/entity",
    "path_init_dir": "init",
    "path_client_dir": "client",

    # Block Entity
    "is_generator": True,
    "stress_capacity": 16.0,
    "generated_speed": 64.0,
    "stress_impact": 8.0,
    "tick_trigger": 100,
    "rpm_threshold": 16.0,
    "procedure": "",

    # Shaft Faces
    "shaft_north": False,
    "shaft_south": False,
    "shaft_east":  False,
    "shaft_west":  False,
    "shaft_up":    False,
    "shaft_down":  False,

    # Renderer Shaft Manual Faces
    "render_shaft_north": False,
    "render_shaft_south": False,
    "render_shaft_east":  False,
    "render_shaft_west":  False,
    "render_shaft_up":    False,
    "render_shaft_down":  False,

    # Shaft Transform per Direction
    "shaft_transform": {
        "NORTH": {"rotate_x": 0.0, "rotate_y": 0.0, "rotate_z": 0.0},
        "SOUTH": {"rotate_x": 0.0, "rotate_y": 0.0, "rotate_z": 0.0},
        "EAST":  {"rotate_x": 0.0, "rotate_y": 0.0, "rotate_z": 0.0},
        "WEST":  {"rotate_x": 0.0, "rotate_y": 0.0, "rotate_z": 0.0},
        "UP":    {"rotate_x": 0.0, "rotate_y": 0.0, "rotate_z": 0.0},
        "DOWN":  {"rotate_x": 0.0, "rotate_y": 0.0, "rotate_z": 0.0},
    },

    # Extras
    "use_cogwheel": False,
    "use_goggle_override": False,

    # Renderer - Shaft
    "render_shaft": False,
    "shaft_model": "SHAFT",
    "shaft_placement": "auto",
    "render_shaft_north": False,
    "render_shaft_south": False,
    "render_shaft_east":  False,
    "render_shaft_west":  False,
    "render_shaft_up":    False,
    "render_shaft_down":  False,
    "multiple_shafts": False,

    # Renderer - Cog
    "render_cog": False,
    "cog_model": "COGWHEEL",

    # Cog transform - her facing için
    "cog_transform": {
        "NORTH": {"rotate_x": 90.0, "rotate_y": 0.0,   "rotate_z": 0.0, "offset_x": 0.0, "offset_y": 0.0, "offset_z": 0.0},
        "SOUTH": {"rotate_x": 90.0, "rotate_y": 180.0, "rotate_z": 0.0, "offset_x": 0.0, "offset_y": 0.0, "offset_z": 0.0},
        "EAST":  {"rotate_x": 90.0, "rotate_y": 0.0,  "rotate_z": 90.0, "offset_x": 0.0, "offset_y": 0.0, "offset_z": 0.0},
        "WEST":  {"rotate_x": 90.0, "rotate_y": 180.0, "rotate_z": 90.0, "offset_x": 0.0, "offset_y": 0.0, "offset_z": 0.0},
        "UP":    {"rotate_x": 0.0,"rotate_y": 0.0,   "rotate_z": 0.0, "offset_x": 0.0, "offset_y": 0.0, "offset_z": 0.0},
        "DOWN":  {"rotate_x": 0.0,"rotate_y": 0.0,  "rotate_z": 0.0, "offset_x": 0.0, "offset_y": 0.0, "offset_z": 0.0},
    },
}

def load_user_config():
    """Kaydedilmiş config varsa yükle, DEFAULT_CONFIG'i güncelle."""
    if os.path.exists(CONFIG_SAVE_PATH):
        try:
            with open(CONFIG_SAVE_PATH, 'r', encoding='utf-8') as f:
                saved = json.load(f)
            DEFAULT_CONFIG.update(saved)
        except Exception:
            pass  # Bozuksa varsayılanla devam

def save_user_config():
    """Mevcut DEFAULT_CONFIG'i diske yaz."""
    try:
        with open(CONFIG_SAVE_PATH, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

# Modül yüklenince otomatik yükle
load_user_config()