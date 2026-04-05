import customtkinter as ctk
from config import DEFAULT_CONFIG, save_user_config

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class SetupDialog(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Kinetic Block Converter - Setup")
        self.geometry("420x320")

        self.confirmed = False
        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(
            self,
            text="⚙  Kinetic Block Converter",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(24, 2))

        ctk.CTkLabel(
            self,
            text="Enter your mod info to continue",
            text_color="gray",
            font=ctk.CTkFont(size=12)
        ).pack(pady=(0, 20))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=40)

        # Mod ID
        ctk.CTkLabel(form, text="Mod ID / namespace:", anchor="w").pack(fill="x", pady=(0, 3))
        self.mod_id_entry = ctk.CTkEntry(form)
        self.mod_id_entry.pack(fill="x", pady=(0, 12))
        # Kaydedilmiş değeri direkt doldur, placeholder yok
        self.mod_id_entry.insert(0, DEFAULT_CONFIG.get("mod_id", ""))

        # Package
        ctk.CTkLabel(form, text="Mod Package name:", anchor="w").pack(fill="x", pady=(0, 3))
        self.package_entry = ctk.CTkEntry(form)
        self.package_entry.pack(fill="x", pady=(0, 4))
        # Kaydedilmiş değeri direkt doldur, placeholder yok
        self.package_entry.insert(0, DEFAULT_CONFIG.get("package_base", ""))

        # Hata label
        self.error_label = ctk.CTkLabel(
            form, text="", text_color="#ff4444", font=ctk.CTkFont(size=11)
        )
        self.error_label.pack(fill="x", pady=(4, 0))

        # Confirm
        ctk.CTkButton(
            self,
            text="Continue →",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self._confirm
        ).pack(fill="x", padx=40, pady=(16, 0))

    def _confirm(self):
        mod_id = self.mod_id_entry.get().strip()
        package = self.package_entry.get().strip()

        if not mod_id:
            self.error_label.configure(text="❌  Mod ID cannot be empty!")
            return
        if not package:
            self.error_label.configure(text="❌  Package name cannot be empty!")
            return
        if " " in mod_id:
            self.error_label.configure(text="❌  Mod ID cannot contain spaces!")
            return
        if " " in package:
            self.error_label.configure(text="❌  Package name cannot contain spaces!")
            return

        # Config güncelle
        DEFAULT_CONFIG["mod_id"] = mod_id
        DEFAULT_CONFIG["package_base"] = package

        # Diske kaydet - bir sonraki açılışta hazır gelsin
        save_user_config()

        self.confirmed = True
        self.withdraw()
        self.quit()