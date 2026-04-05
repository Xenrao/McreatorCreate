import os
import shutil


class BlockGenerator:
    def __init__(self, transformer, input_path):
        self.transformer = transformer
        self.input_path = input_path

    def generate(self, undo_manager=None):
        content = self.transformer.transform()

        # Backup al (undo için)
        if undo_manager and os.path.exists(self.input_path):
            undo_manager.track_modified(self.input_path)

        with open(self.input_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return self.input_path