# verify_dialog.py
import sys
from PyQt6.QtWidgets import QApplication
from ui.dialogs import AutoTagDialog

def main():
    """
    This script creates and shows the AutoTagDialog directly for verification.
    """
    app = QApplication(sys.argv)

    # Create the dialog with a dummy folder path
    dialog = AutoTagDialog(folder_path="G:\\DUMMY\\FOLDER", parent=None)

    # Load some sample tags to simulate a real-world scenario
    sample_tags = ["Action", "Sci-Fi", "Rendered", "ProjectFile"]
    dialog.load_current = lambda: dialog.tag_input_area.set_tags(sample_tags)
    dialog.load_current()

    dialog.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()
