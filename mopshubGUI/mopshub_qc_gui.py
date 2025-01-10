########################################################
"""
    This file is part of the MOPS-Hub project.
    Author: Ahmed Qamesh (University of Wuppertal)
    email: ahmed.qamesh@cern.ch  
    Date: 01.05.2023
"""
########################################################
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit
from PyQt5.QtGui import QColor

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Test GUI')

        # Buttons
        self.uart_button = self.create_test_button('UART Test')
        self.can_button = self.create_test_button('CAN Test')
        self.led_button = self.create_test_button('LED Test')
        self.memory_button = self.create_test_button('Memory Test')

        # LEDs
        self.led_pass = self.create_led_label('Pass', QColor('green'))
        self.led_fail = self.create_led_label('Fail', QColor('red'))

        # Output Screen
        self.output_screen = QTextEdit()
        self.output_screen.setReadOnly(True)

        # Log File Button
        self.log_button = QPushButton('Save Log')
        self.log_button.clicked.connect(self.save_log)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.uart_button)
        layout.addWidget(self.can_button)
        layout.addWidget(self.led_button)
        layout.addWidget(self.memory_button)
        layout.addWidget(self.led_pass)
        layout.addWidget(self.led_fail)
        layout.addWidget(self.output_screen)
        layout.addWidget(self.log_button)

        self.setLayout(layout)

        # Test functions
        self.uart_button.clicked.connect(self.run_uart_test)
        self.can_button.clicked.connect(self.run_can_test)
        self.led_button.clicked.connect(self.run_led_test)
        self.memory_button.clicked.connect(self.run_memory_test)

    def create_test_button(self, text):
        button = QPushButton(text)
        return button

    def create_led_label(self, text, color):
        led_label = QLabel(text)
        led_label.setStyleSheet(f'background-color: {color.name()}')
        return led_label

    def save_log(self):
        log_content = self.output_screen.toPlainText()
        with open('test_log.txt', 'w') as log_file:
            log_file.write(log_content)

    def run_uart_test(self):
        # Replace this with your UART test logic
        self.output_screen.append('Running UART Test...')
        # Assume the test passed for now
        self.led_pass.show()
        self.led_fail.hide()

    def run_can_test(self):
        # Replace this with your CAN test logic
        self.output_screen.append('Running CAN Test...')
        # Assume the test failed for now
        self.led_pass.hide()
        self.led_fail.show()

    def run_led_test(self):
        # Replace this with your LED test logic
        self.output_screen.append('Running LED Test...')
        # Assume the test passed for now
        self.led_pass.show()
        self.led_fail.hide()

    def run_memory_test(self):
        # Replace this with your memory test logic
        self.output_screen.append('Running Memory Test...')
        # Assume the test failed for now
        self.led_pass.hide()
        self.led_fail.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())
