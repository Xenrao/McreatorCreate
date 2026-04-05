import os
import shutil
import json


class UndoManager:
    """Oluşturulan dosyaları takip eder, undo için backup saklar"""

    def __init__(self):
        self.created_files = []      # Yeni oluşturulan dosyalar
        self.backup_files = {}       # original_path -> backup_path
        self.has_undo = False

    def reset(self):
        self.created_files = []
        self.backup_files = {}
        self.has_undo = False

    def track_created(self, path: str):
        """Yeni oluşturulan dosyayı kaydet"""
        self.created_files.append(path)

    def track_modified(self, original_path: str):
        """Değiştirilen dosyanın backup'ını al"""
        if not os.path.exists(original_path):
            return
        backup_path = original_path + ".undo_backup"
        shutil.copy2(original_path, backup_path)
        self.backup_files[original_path] = backup_path

    def undo(self) -> list:
        """
        - Yeni oluşturulan dosyaları sil
        - Değiştirilen dosyaları eski haline döndür
        Yapılan işlemleri log olarak döndür
        """
        log = []

        # Yeni dosyaları sil
        for path in self.created_files:
            if os.path.exists(path):
                os.remove(path)
                log.append(f"🗑  Deleted: {os.path.basename(path)}")
            else:
                log.append(f"⚠️  Not found: {os.path.basename(path)}")

        # Boş kalan klasörleri temizle
        dirs_to_check = set(os.path.dirname(p) for p in self.created_files)
        for d in dirs_to_check:
            if os.path.exists(d) and not os.listdir(d):
                os.rmdir(d)
                log.append(f"🗑  Removed empty dir: {os.path.basename(d)}")

        # Backup'ları geri yükle
        for original_path, backup_path in self.backup_files.items():
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, original_path)
                os.remove(backup_path)
                log.append(f"↩️  Restored: {os.path.basename(original_path)}")
            else:
                log.append(f"⚠️  Backup not found: {os.path.basename(backup_path)}")

        self.reset()
        return log

    def cleanup_backups(self):
        """Backup dosyalarını temizle (başarılı convert sonrası)"""
        for backup_path in self.backup_files.values():
            if os.path.exists(backup_path):
                os.remove(backup_path)