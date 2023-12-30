from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
import sqlite3
import requests
import base64
from PyQt6 import uic
from PyQt6 import QtWidgets
from PyQt6 import QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QStyledItemDelegate, QApplication, QMainWindow, QPushButton, QLabel
import sys
from threading import Thread

def find_elements(driver:webdriver.Chrome, by, value:str)->list[WebElement]:
    while True:
        elements = driver.find_elements(by, value)
        if len(elements) > 0:
            return elements
        # sleep(0.1)

def find_element(driver:webdriver.Chrome, by, value:str)->WebElement:
    while True:
        try:
            element = driver.find_element(by, value)
            return element
        except:
            pass
        sleep(0.1)

Ui_MainWindow, QtBaseClass = uic.loadUiType('window.ui')
class CenterDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter
        super().paint(painter, option, index)

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.start_button = self.findChild(QPushButton, 'start_button')
        self.start_button.clicked.connect(self.start_button_clicked)
        self.stop_button = self.findChild(QPushButton, 'stop_button')
        self.stop_button.clicked.connect(self.stop_button_clicked)
        self.resume_button = self.findChild(QPushButton, 'resume_button')
        self.resume_button.clicked.connect(self.resume_button_clicked)
        self.current_url_label = self.findChild(QLabel, 'current_url')
        self.docs_count_label = self.findChild(QLabel, 'docs_count')
        self.progress_label = self.findChild(QLabel, 'progress')

        self.current_url_label.setText('')
        self.docs_count_label.setText('0')
        self.progress_label.setText('Stopped')

        self.process = Thread(target=self.main)

        self.is_allowed_to_run = True
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()

    def start_button_clicked(self):
        self.process = Thread(target=self.main)
        self.is_allowed_to_run = True
        self.process.start()
        self.progress_label.setText('Running')

    def stop_button_clicked(self):
        self.is_allowed_to_run  = False
        self.progress_label.setText('Stopped')

    def resume_button_clicked(self):
        self.progress_label.setText('Resumed')

    def main(self):
        connection = sqlite3.connect("database.db")
        cursor = connection.cursor()

        cursor.execute('DELETE FROM crawl_table')
        cursor.execute('DELETE FROM pdf_table')
        connection.commit()

        results = []
        # products = ['sales', 'service', 'marketing', 'commerce', 'analytics', 'platform', 'experience', 'einstein', 'crossproduct', 'financialservices', 'health', 'manufacturing']
        products = ['sales']
       
        if not self.is_allowed_to_run:
            return
        
        for product in products:
            if not self.is_allowed_to_run:
                return
        
            url = f'https://help.salesforce.com/s/products/sales?language=en_US'
            self.driver.get(url)
            self.current_url_label.setText(url)
            while True:
                try:
                    doc_count = int(self.driver.find_element(By.XPATH, '/html/body/div[4]/div/div[2]/div/div[1]/div/div/c-hc-product-landing/div/div[2]/div').text.split(' ')[0])
                    if doc_count > 0:
                        break
                except:
                    pass
                sleep(0.1)
            self.docs_count_label.setText(f'{doc_count}')
            for i in range(1, doc_count + 1):              
                tile = find_element(self.driver, By.XPATH, f'/html/body/div[4]/div/div[2]/div/div[1]/div/div/c-hc-product-landing/div/div[2]/c-hc-doc-tile[{i}]/div')
                title_url = find_element(tile, By.CLASS_NAME, 'tile-title').get_attribute('href')
                try:
                    down_url = tile.find_element(By.CLASS_NAME, 'download-icon').get_attribute('href')
                except:
                    down_url = ''
                results.append({"title_url" : title_url, "down_url" : down_url})
                print(title_url, down_url)
        for index, item in enumerate(results):
            self.docs_count_label.setText(f'{len(results)}({index + 1})')
            if not self.is_allowed_to_run:
                return
        
            title_url = item["title_url"]
            if '.pdf' in title_url:
                content = None
                page_source = None
                print(page_source)
            else:                                             
                self.driver.get(title_url)
                content = find_element(self.driver, By.XPATH, '//*[@id="content"]').text
                page_source = self.driver.page_source

            down_url = item["down_url"]
            if down_url != '':
                response = requests.get(down_url)
                pdf_blob1 = base64.b64encode(response.content)
            else:
                pdf_blob1 = None
                print(pdf_blob1)
            cursor.execute("insert into crawl_table(url, html, content, pdf_id) values(?,?,?,?)", (title_url, page_source, content, index))
            cursor.execute("insert into pdf_table(id, link, pdf_blob) values(?,?,?)", (index, down_url, pdf_blob1))
            connection.commit()

# main function
if __name__ == "__main__":
     app = QApplication([])
     window = MainWindow()
     window.show()
     sys.exit(app.exec())