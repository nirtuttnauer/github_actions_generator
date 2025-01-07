# main.py
import sys
from PyQt5.QtWidgets import QApplication
from YamlEditor import GitHubActionsEditor
def main():
    app = QApplication(sys.argv)
    window = GitHubActionsEditor()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()