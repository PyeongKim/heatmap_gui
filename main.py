from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import QThread, pyqtSignal, QObject, pyqtSlot, Qt
import sys
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import style
import seaborn as sns
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QPixmap
style.use('ggplot')


class CountWorker(QObject):

    @pyqtSlot()
    def proc_counter(self):  # A slot takes no params
        pass
        #self.finished.emit()


class PopUpProgressB(QWidget):

    def __init__(self):
        super().__init__()
        self.pbar = QProgressBar(self)
        self.pbar.setRange(0, 0)

        self.pbar.setGeometry(100, 200, 200, 75)
        self.setGeometry(50, 50, 150, 100)
        self.label1 = QLabel('Loading file, please wait.', self)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label1)
        self.layout.addWidget(self.pbar)
        self.setLayout(self.layout)
        self.center()
        self.setWindowTitle('Loading...')
        # self.show()

        self.obj = CountWorker()
        self.thread = QThread()
        self.obj.moveToThread(self.thread)
          # To hide the progress bar after the progress is completed
        self.thread.started.connect(self.obj.proc_counter)
        # self.thread.start()  # This was moved to start_progress

    def start_progress(self):  # To restart the progress every time
        self.show()
        self.thread.start()

    def stop_progress(self):
        self.thread.quit()
        self.hide()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


class CSVWorker(QThread, QWidget):
    started = pyqtSignal()
    finished = pyqtSignal(dict)
    stop = pyqtSignal()
    def set_input(self, filePath):
        self.filePath = filePath
    def run(self):
        self.started.emit()
        data = {}

        data['filepath'] = str(self.filePath)

        if self.filePath.split('.')[-1]  == 'xlsx':
            df = pd.read_excel(str(self.filePath))
        elif self.filePath.split('.')[-1]  == 'csv':
            df = pd.read_csv(str(self.filePath))
        elif self.filePath.split('.')[-1]  in ['tab','tsv']:
            df = pd.read_csv(str(self.filePath), sep='\t')

        data['df'] = df

        self.finished.emit(data)
        self.stop.emit()

class PlotWorker(QThread, QWidget):
    started = pyqtSignal()
    finished = pyqtSignal(dict)

    def set_input(self, filePath):
        self.filePath = filePath
    def run(self):
        self.started.emit()
        data = {}

        data['filepath'] = str(self.filePath)
        try:
            if self.filePath.split('.')[-1]  == 'xlsx':
                df = pd.read_excel(str(self.filePath))
            elif self.filePath.split('.')[-1]  == 'csv':
                df = pd.read_csv(str(self.filePath))
            elif self.filePath.split('.')[-1]  in ['tab','tsv']:
                df = pd.read_csv(str(self.filePath), sep='\t')

            data['df'] = df
        except:
            data['df'] = None
        finally:
            self.finished.emit(data)
            self.stop.emit()


class MainWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        self.setGeometry(50, 50, 400, 400)
        self.center()
        self.setWindowTitle('Heatmap Generator')

        #Grid Layout
        grid = QGridLayout()
        self.setLayout(grid)
        self.df = pd.DataFrame([])

        self.popup = PopUpProgressB()

        self.csvload = CSVWorker()
        self.csvload.started.connect(self.inactivate_button)
        self.csvload.finished.connect(self.load_csv)
        self.csvload.finished.connect(self.csvload.quit)
        self.csvload.finished.connect(self.popup.stop_progress)



        #Import CSV Button
        self.btn1 = QPushButton('Import File', self)
        self.btn1.resize(self.btn1.sizeHint())
        self.btn1.clicked.connect(self.openfile)

        grid.addWidget(self.btn1, 0, 1)

        self.lineEdit = QLineEdit(self)
        self.lineEdit.setEnabled(False)
        grid.addWidget(self.lineEdit, 0, 0)

        # select gene column
        self.comboBox = QComboBox(self)
        grid.addWidget(self.comboBox, 1, 1)
        label1 = QLabel('Select Gene Column:', self)
        grid.addWidget(label1, 1, 0)

        # color map select
        self.cmap_list = ["coolwarm","spectral","vlag","viridis","rocket", "mako","crest",'magma','flare']
        self.comboBox2 = QComboBox(self)
        self.comboBox2.addItems(self.cmap_list)
        self.comboBox2.currentIndexChanged.connect(self.changeimage)
        grid.addWidget(self.comboBox2, 2, 1)
        label2 = QLabel('Select Colour Map:', self)
        grid.addWidget(label2, 2, 0)

        self.cmap_label = QLabel(self)
        pixmap = QPixmap('./data/{}.png'.format(self.comboBox2.currentText()))
        pixmap = pixmap.scaled(20, 100, Qt.KeepAspectRatio, Qt.FastTransformation)
        self.cmap_label.setPixmap(pixmap)
        #
        self.cmap_label.setScaledContents(True)
        self.cmap_label.setFixedHeight(20)
        grid.addWidget(self.cmap_label, 3, 1)
        # y_cluster
        self.column_cluster = QComboBox(self)
        self.column_cluster.addItems(['True', 'False'])
        grid.addWidget(self.column_cluster, 4, 1)
        label6 = QLabel('Show column cluster:', self)
        grid.addWidget(label6, 4, 0)

        # x_cluster
        self.row_cluster = QComboBox(self)
        self.row_cluster.addItems(['True', 'False'])
        grid.addWidget(self.row_cluster, 5, 1)
        label7 = QLabel('Show row cluster:', self)
        grid.addWidget(label7, 5, 0)

        # x size
        self.fig_size_x = QLineEdit(self)
        self.fig_size_x.setText('10')
        grid.addWidget(self.fig_size_x, 6, 1)
        label3 = QLabel('Select figure width:', self)
        grid.addWidget(label3, 6, 0)

        # y size
        self.fig_size_y = QLineEdit(self)
        self.fig_size_y.setText('10')
        grid.addWidget(self.fig_size_y, 7, 1)
        label4 = QLabel('Select figure hieght:', self)
        grid.addWidget(label4, 7, 0)

        # font size
        self.font_scale = QLineEdit(self)
        self.font_scale.setText('1.0')
        grid.addWidget(self.font_scale, 8, 1)
        label5 = QLabel('Select font scale:', self)
        grid.addWidget(label5, 8, 0)



        # dpi
        self.dpi = QLineEdit(self)
        self.dpi.setText('600')
        grid.addWidget(self.dpi, 9, 1)
        label8 = QLabel('Select dpi:', self)
        grid.addWidget(label8, 9, 0)

        #Plot Button
        self.btn2 = QPushButton('Generate Plot', self)
        self.btn2.resize(self.btn2.sizeHint())
        self.btn2.clicked.connect(self.plot)
        grid.addWidget(self.btn2, 10, 0, 1, 2)


        self.setLayout(grid)

        self.show()

    def changeimage(self):
        pixmap = QPixmap('./data/{}.png'.format(self.comboBox2.currentText()))
        pixmap = pixmap.scaled(20, 100, Qt.KeepAspectRatio, Qt.FastTransformation)
        self.cmap_label.setPixmap(pixmap)

    def openfile(self):
        filePath, _ = QFileDialog.getOpenFileName(self, 'Open file', '/home')
        if filePath != "" and filePath.split('.')[-1] in ['csv', 'xlsx', 'tsv', 'tab']:
            self.popup.start_progress()
            self.csvload.set_input(filePath)
            self.csvload.start()
        elif not filePath.split('.')[-1] in ['csv', 'xlsx', 'tsv', 'tab'] and filePath != '':
            QMessageBox.critical(self, "Error", "You have to upload one of following extensions: \n csv, tsv, xlsx, and tab")
        else:
            QMessageBox.warning(self, "Warning", "You did not load your file!")

    def inactivate_button(self):
        self.btn1.setEnabled(False)



    @pyqtSlot(dict)
    def load_csv(self, data):
        if data != None:
            filePath = data['filepath']
            self.lineEdit.setText('{}'.format(filePath))
            self.df = data['df']
            self.all_columns = list(self.df)
            self.comboBox.addItems(self.all_columns)

            QMessageBox.information(self, 'Completed', "Loaded file from {}".format(filePath))
        else:
            QMessageBox.critical(self, "Error", "Ooops! Something went wrong. Please check your file.")
        self.btn1.setEnabled(True)

    def plot(self):
        self.btn2.setEnabled(False)
        if self.df.shape[0] != 0:
            name, _ = QFileDialog.getSaveFileName(self, 'Save File')
            if name != '':

                plt.cla()
                gene_colomn = self.comboBox.currentText()
                heatmap_HEM_MAT=pd.pivot_table(self.df, index=gene_colomn, values=list(self.df).remove(gene_colomn))

                sns.set(font_scale=float(self.font_scale.text())) #font size
                col_cluster = 0 if str(self.column_cluster.currentText()) == 'False' else 1
                row_cluster = 0 if str(self.row_cluster.currentText()) == 'False' else 1
                sns.clustermap(heatmap_HEM_MAT,
                               cmap=str(self.comboBox2.currentText()),
                               yticklabels=True,
                               z_score=0,
                               cbar_kws={},
                               col_cluster=bool(col_cluster),
                               row_cluster=bool(row_cluster),
                               figsize=(int(self.fig_size_x.text()), int(self.fig_size_y.text()))) #making heatmap


                plt.savefig(name, dpi=int(self.dpi.text()))
                QMessageBox.about(self, "Completed", "Heatmap saved to {}".format(name))
            else:
                QMessageBox.warning(self, 'Warning','You did not designated file name to save! Please designate file name (either .pdf or .png)')
        else:
            QMessageBox.critical(self, "Error", "Please upload your file")
        self.btn2.setEnabled(True)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())




def main():
    app = QApplication(sys.argv)
    w = MainWidget()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
