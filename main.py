from ui.setup_dialog import SetupDialog
from ui.main_window import MainWindow

if __name__ == "__main__":
    setup = SetupDialog()
    setup.mainloop()

    if setup.confirmed:
        app = MainWindow()
        app.mainloop()