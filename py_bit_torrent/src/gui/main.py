from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QTextEdit,
    QProgressBar,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
)
from PySide6.QtCore import QTimer
import sys
from py_bit_torrent.parse_torrent import parse_torrent
from py_bit_torrent.torrent import MetaInfoStruct


class BitTorrentUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BitTorrent Client")
        self.setMinimumSize(800, 600)
        self.torrent_info = None

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create button row
        button_layout = QHBoxLayout()

        # Torrent file selection button
        self.select_file_btn = QPushButton("Select Torrent File")
        self.select_file_btn.clicked.connect(self.select_torrent_file)
        button_layout.addWidget(self.select_file_btn)

        # Start/Pause button
        self.start_pause_btn = QPushButton("Start")
        self.start_pause_btn.setEnabled(False)
        self.start_pause_btn.clicked.connect(self.toggle_download)
        button_layout.addWidget(self.start_pause_btn)

        # Stop button
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_download)
        button_layout.addWidget(self.stop_btn)

        layout.addLayout(button_layout)

        # Create status section
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Status: Idle")
        status_layout.addWidget(self.status_label)

        self.speed_label = QLabel("Speed: 0 KB/s")
        status_layout.addWidget(self.speed_label)

        self.peers_label = QLabel("Peers: 0")
        status_layout.addWidget(self.peers_label)

        layout.addLayout(status_layout)

        # Create progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Create torrent info table
        self.create_torrent_table()
        layout.addWidget(self.torrent_table)

        # Create text area for logs
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)

        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_stats)
        self.update_timer.start(1000)  # Update every second

        self.is_downloading = False

    def create_torrent_table(self):
        self.torrent_table = QTableWidget()
        self.torrent_table.setColumnCount(4)
        self.torrent_table.setHorizontalHeaderLabels(
            ["Name", "Size", "Progress", "Status"]
        )
        header = self.torrent_table.horizontalHeader()
        header.setSectionResizeMode(0, header.ResizeMode.Stretch)

    def select_torrent_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Torrent File", "", "Torrent Files (*.torrent)"
        )

        if file_name:
            try:
                self.torrent_info = parse_torrent(file_name)
                self.display_torrent_info(self.torrent_info)
                self.start_pause_btn.setEnabled(True)
                self.stop_btn.setEnabled(True)
                self.log_message(f"Loaded torrent file: {file_name}")
            except Exception as e:
                self.log_message(f"Error reading torrent file: {str(e)}")

    def display_torrent_info(self, torrent_info: MetaInfoStruct):
        self.torrent_table.setRowCount(0)

        if "info" in torrent_info:
            info = torrent_info["info"]

            if "length" in info:
                # Single file torrent
                self.add_torrent_row(
                    info.get("name", "N/A"),
                    self.format_size(info["length"]),
                    "0%",
                    "Ready",
                )
            elif "files" in info:
                # Multiple files torrent
                for file in info["files"]:
                    self.add_torrent_row(
                        file.get("path", ["N/A"])[-1],
                        self.format_size(file.get("length", 0)),
                        "0%",
                        "Ready",
                    )

    def add_torrent_row(self, name, size, progress, status):
        row = self.torrent_table.rowCount()
        self.torrent_table.insertRow(row)
        self.torrent_table.setItem(row, 0, QTableWidgetItem(name))
        self.torrent_table.setItem(row, 1, QTableWidgetItem(size))
        self.torrent_table.setItem(row, 2, QTableWidgetItem(progress))
        self.torrent_table.setItem(row, 3, QTableWidgetItem(status))

    def toggle_download(self):
        self.is_downloading = not self.is_downloading
        if self.is_downloading:
            self.start_download()
        else:
            self.pause_download()

    def start_download(self):
        self.start_pause_btn.setText("Pause")
        self.status_label.setText("Status: Downloading")
        self.log_message("Starting download...")
        # Add actual download logic here

    def pause_download(self):
        self.start_pause_btn.setText("Resume")
        self.status_label.setText("Status: Paused")
        self.log_message("Download paused")
        # Add pause logic here

    def stop_download(self):
        self.is_downloading = False
        self.start_pause_btn.setText("Start")
        self.status_label.setText("Status: Stopped")
        self.progress_bar.setValue(0)
        self.log_message("Download stopped")
        # Add stop logic here

    def update_stats(self):
        if self.is_downloading:
            # Add actual stats update logic here
            # For now, just simulate progress
            current = self.progress_bar.value()
            if current < 100:
                self.progress_bar.setValue(current + 1)

    def log_message(self, message: str):
        self.log_text.append(f"> {message}")

    @staticmethod
    def format_size(size_in_bytes: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size_in_bytes < 1024:
                return f"{size_in_bytes:.2f} {unit}"
            size_in_bytes /= 1024
        return f"{size_in_bytes:.2f} TB"


def main():
    app = QApplication(sys.argv)
    window = BitTorrentUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
