# -*- coding: utf-8 -*-
'''
Created on Sun Jul  5 21:59:36 2020

@author: Babi
@coauthor: leonardojacomussi

Lasted edition on Mon Jul  20 13:04:22 2020
'''

# Garante a reprodução no diretório
import librosa
from queue import Queue
import sounddevice as sd
from itertools import count
from gtts import gTTS  # google text to speech
from PyQt5 import QtCore, QtGui, QtWidgets
from numpy import ndarray, round as rd
import os
import time
p = os.path.join(os.path.dirname(__file__))  # 'ttsApp_v1.py'


# pip install librosa==0.7.2
# se a versão do numba >= 0.48.0: ajuste o arquivo "decorators.py"
# (exemplo de caminho: "C:\ProgramData\Anaconda3\Lib\site-packages\librosa\util\decorators.py")
#       old: from numba.decorators import jit as optional_jit
#       new: from numba.core.decorators import jit as optional_jit
# caso aponte algum erro de formato desconhecido ao tentar abrir algum áudio com librosa.load(), faça:
#       conda install -c conda-forge ffmpeg

# %% Audio device information

def query_devices():
    ''''
    Função que retorna os dispositivos de áudio conectados ao computador,
    separando os dispositivos de entrada e de saída, bem como determina o
    dispositivo padrão definido pelo sistema para cada caso (entrada e saída).

    Returns
    -------
    dev : dict
        Dicionário com as informações dos dispositivos de áudio de entrada e
        saída.
    '''
    try:
        dev = sd.query_devices()
        inputDefault = sd.default.device[0]
        outputDefault = sd.default.device[1]
        inputDevices = []
        outputDevices = []
        inCount = 0
        outCount = 0

        for i in range(len(dev)):
            # Encontrando dispositivos com canais de entrada
            if dev[i]['max_input_channels'] > 0:
                inputDevices.append(dev[i])
                # Encontrando dispositivo de entrada padrão
                if i == outputDefault:
                    inputDefault = inCount
                else:
                    inCount += 1
            else:
                pass
            # Encontrando dispositivos com canais de saída
            if dev[i]['max_output_channels'] > 0:
                outputDevices.append(dev[i])
                # Encontrando dispositivo de saída padrão
                if i == outputDefault:
                    outputDefault = outCount
                else:
                    outCount += 1
            else:
                pass
        dev = {'in': inputDevices,
               'inDefault': inputDefault,
               'out': outputDevices,
               'outDefault': outputDefault}
        return dev
    except Exception as E:
        print("query_devices(): ", E, "\n")


def getInfosDevice(device):
    '''
    Função que retorna as taxas de amostragem e números de canais suportados pelo
    dispositivo de saída.
    Para verificar as condições do dispositivo de entrada deve-se alterar o check
    do sounddevice para: sd.check_input_settings

    Parameters
    ----------
    device : int
        Número do dispositivo de áudio obtido pela função query_devices().

    Returns
    -------
    infos : dict
        Dicionário contendo taxas de amostragem e número de canais suportados.
    '''
    try:
        d = trueDevice(0, device)
        device = d[1]
        # Check sampling rates
        samplerates = 16000, 24000, 32000, 44100, 48000, 96000, 128000
        supported_samplerates = []
        for fs in samplerates:
            try:
                sd.check_output_settings(device=device, samplerate=fs)
            except:
                pass
            else:
                supported_samplerates.append(fs)
        # Check output channels
        supported_outChannels = []
        for ch in range(60):
            try:
                sd.check_output_settings(device=device, channels=ch)
            except:
                # print(ch, e)
                pass
            else:
                supported_outChannels.append(ch)

        # Information in a dictionary.
        infos = {'sampleRate': supported_samplerates,
                 'outChannels': supported_outChannels}
        return infos
    except Exception as E:
        print("getInfosDevice(): ", E, "\n")


def trueDevice(inDev, outDev):
    '''
    Parameters
    ----------
    device : int
        Número do dispositivo de áudio obtido pela função query_devices().

    Returns
    -------
    d : list
    Verdadeiro número do dispositivo de áudio contido em 
    sounddevice.query_devices().
    '''
    try:
        _dev = query_devices()
        sdDevice = sd.query_devices()
        for i in range(len(sdDevice)-1):
            if _dev['in'][inDev] == sdDevice[i]:
                ind = i
            else:
                pass
            if _dev['out'][outDev] == sdDevice[i]:
                outd = i
            else:
                pass
        d = [ind, outd]
        return d
    except Exception as E:
        print("trueDevice(): ", E, "\n")


def init_device():
    '''
    Função que retorna as informações dos dispositivos de áudio conectados ao
    computador, condicionando de forma conveniente para acesso facilitado nos 
    métodos da aplicação em questão.

    Returns
    -------
    dev : dict
        Dicionário com as informações dos dispositivos de áudio de entrada e
        saída.
    devDefault : int
        Número do dispositivo de saída default, definido pelo sounddevice.
    infosDev : dict
        Dicionário contendo taxas de amostragem e número de canais suportados.
    sampleDefault : int
        Taxa de amostragem do dispositivo de aúdio padrão 'devDefault'.
    numChannels : int
        Número máximo de canais suportados pelo dispositivo de áudio padrão 'devDefault'.
    outChannels : list
        Lista de canais ativos para reprodução de áudio.
    audioFormat : str
        Formato de áudio a ser salvo para o usuário.
    sd_device : list
        Número dos dispositivos de áudio padrões interpretados pelo sounddevice.

    '''
    try:
        # Lista de dispositivos pelo SoundDevice - var: dev
        dev = query_devices()
        # Dispositivo padrão detectado pelo SoundDevice - var: devDefault
        devDefault = dev['outDefault']
        # Coletando informações sobre o dispositivo - var: infosDev
        infosDev = getInfosDevice(devDefault)
        # Setando taxa de amostragem - var: sampleDefault
        if 24000 in infosDev['sampleRate']:
            sampleDefault = 24000
        elif 44100 in infosDev['sampleRate']:
            sampleDefault = infosDev['sampleRate']
        elif 48000 in infosDev['sampleRate']:
            sampleDefault = infosDev['sampleRate']
        else:
            sampleDefault = infosDev['sampleRate']
        # Setando canais de saída - var: outChannels
        numChannels = dev['out'][devDefault]['max_output_channels']
        outChannels = []
        for i in range(numChannels):
            if i == 0 or i == 1:
                ch = i + 1
                outChannels.append(ch)
        # Fomato do arquivo de áudio - var: audioFormat
        audioFormat = 'mp3'
        # Número "verdadeiro" do dispositivo usado na stream do soundDevice - var: sd_device
        sd_device = trueDevice(dev['inDefault'], devDefault)
        return dev, devDefault, infosDev, sampleDefault,\
            numChannels, outChannels, audioFormat, sd_device
    except Exception as E:
        print("init_device(): ", E, "\n")

# %% Class guiMain


class guiMain(object):
    '''
    Classe guiMain
    Instancia itens gráficos contidos na janela principal do app.
    Gerada utilizando o software Qt designer:
        https://build-system.fman.io/qt-designer-download
    '''

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 538)
        MainWindow.setWindowIcon(QtGui.QIcon(p+'\\icon_5.ico'))
        MainWindow.setStyleSheet("background-color: rgb(75, 75, 75);")
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.textEntry = QtWidgets.QTextEdit(self.centralwidget)
        self.textEntry.setGeometry(QtCore.QRect(10, 140, 601, 231))
        font = QtGui.QFont()
        font.setFamily("Sitka Small")
        font.setPointSize(14)
        self.textEntry.setFont(font)
        self.textEntry.setStyleSheet("background-color: None;")
        self.textEntry.setObjectName("textEntry")
        self.btnSynthesize = QtWidgets.QPushButton(self.centralwidget)
        self.btnSynthesize.setGeometry(QtCore.QRect(620, 140, 171, 111))
        font = QtGui.QFont()
        font.setFamily("Sitka Small")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.btnSynthesize.setFont(font)
        self.btnSynthesize.setStyleSheet(
            "background-color: rgb(108, 216, 255);")
        self.btnSynthesize.setIcon(QtGui.QIcon(p+'\\icon_synthesize.ico'))
        self.btnSynthesize.setIconSize(QtCore.QSize(60, 60))
        self.btnSynthesize.setObjectName("btnSynthesize")
        self.btnClear = QtWidgets.QPushButton(self.centralwidget)
        self.btnClear.setGeometry(QtCore.QRect(620, 320, 171, 51))
        font = QtGui.QFont()
        font.setFamily("Sitka Small")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.btnClear.setFont(font)
        self.btnClear.setStyleSheet("background-color: rgb(108, 216, 255);")
        self.btnClear.setIcon(QtGui.QIcon(p+'\\icon_clear.ico'))
        self.btnClear.setIconSize(QtCore.QSize(60, 60))
        self.btnClear.setObjectName("btnClear")
        self.btnPlay = QtWidgets.QPushButton(self.centralwidget)
        self.btnPlay.setGeometry(QtCore.QRect(30, 429, 60, 60))
        font = QtGui.QFont()
        font.setFamily("Sitka Small")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.btnPlay.setFont(font)
        self.btnPlay.setStyleSheet("background-color: rgb(128, 255, 171);")
        self.btnPlay.setText("")
        self.btnPlay.setIcon(QtGui.QIcon(p+'\\icon_play.ico'))
        self.btnPlay.setIconSize(QtCore.QSize(80, 80))
        self.btnPlay.setObjectName("btnPlay")
        self.btnPause = QtWidgets.QPushButton(self.centralwidget)
        self.btnPause.setGeometry(QtCore.QRect(260, 429, 60, 60))
        font = QtGui.QFont()
        font.setFamily("Sitka Small")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.btnPause.setFont(font)
        self.btnPause.setStyleSheet("background-color: rgb(255, 251, 124);")
        self.btnPause.setText("")
        self.btnPause.setIcon(QtGui.QIcon(p+'\\icon_pause.ico'))
        self.btnPause.setIconSize(QtCore.QSize(80, 80))
        self.btnPause.setObjectName("btnPause")
        self.btnStop = QtWidgets.QPushButton(self.centralwidget)
        self.btnStop.setGeometry(QtCore.QRect(520, 429, 60, 60))
        font = QtGui.QFont()
        font.setFamily("Sitka Small")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.btnStop.setFont(font)
        self.btnStop.setStyleSheet("background-color: rgb(255, 99, 101);")
        self.btnStop.setText("")
        self.btnStop.setIcon(QtGui.QIcon(p+'\\icon_stop.ico'))
        self.btnStop.setIconSize(QtCore.QSize(80, 80))
        self.btnStop.setObjectName("btnStop")
        self.lblTitle = QtWidgets.QLabel(self.centralwidget)
        self.lblTitle.setGeometry(QtCore.QRect(160, 40, 441, 41))
        font = QtGui.QFont()
        font.setFamily("Palatino Linotype")
        font.setPointSize(24)
        font.setBold(True)
        font.setWeight(75)
        self.lblTitle.setFont(font)
        self.lblTitle.setStyleSheet("color: rgb(108, 216, 255);")
        self.lblTitle.setObjectName("lblTitle")
        self.lblEnterTxt = QtWidgets.QLabel(self.centralwidget)
        self.lblEnterTxt.setGeometry(QtCore.QRect(10, 110, 221, 31))
        font = QtGui.QFont()
        font.setFamily("Sitka Small")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.lblEnterTxt.setFont(font)
        self.lblEnterTxt.setStyleSheet("color: rgb(108, 216, 255);")
        self.lblEnterTxt.setObjectName("lblEnterTxt")
        self.lblStatus = QtWidgets.QLabel(self.centralwidget)
        self.lblStatus.setGeometry(QtCore.QRect(10, 380, 271, 31))
        font = QtGui.QFont()
        font.setFamily("Sitka Small")
        font.setPointSize(14)
        self.lblStatus.setFont(font)
        self.lblStatus.setStyleSheet("color: rgb(0, 255, 0);")
        self.lblStatus.setObjectName("lblStatus")
        self.lblTime = QtWidgets.QLabel(self.centralwidget)
        self.lblTime.setGeometry(QtCore.QRect(340, 380, 271, 31))
        font = QtGui.QFont()
        font.setFamily("Sitka Small")
        font.setPointSize(14)
        self.lblTime.setFont(font)
        self.lblTime.setStyleSheet("color: rgb(108, 216, 255);")
        self.lblTime.setObjectName("lblTime")
        self.btnSetup = QtWidgets.QPushButton(self.centralwidget)
        self.btnSetup.setGeometry(QtCore.QRect(620, 260, 171, 51))
        font = QtGui.QFont()
        font.setFamily("Sitka Small")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.btnSetup.setFont(font)
        self.btnSetup.setStyleSheet("background-color: rgb(108, 216, 255);")
        self.btnSetup.setIcon(QtGui.QIcon(p+'\\icon_settings.ico'))
        self.btnSetup.setIconSize(QtCore.QSize(45, 45))
        self.btnSetup.setObjectName("btnSetup")
        self.progressBar = QtWidgets.QSlider(self.centralwidget)
        self.progressBar.setGeometry(QtCore.QRect(30, 510, 551, 22))
        self.progressBar.setOrientation(QtCore.Qt.Horizontal)
        self.progressBar.setObjectName("progressBar")
        self.lblDuration = QtWidgets.QLabel(self.centralwidget)
        self.lblDuration.setGeometry(QtCore.QRect(600, 500, 141, 31))
        font = QtGui.QFont()
        font.setFamily("Sitka Small")
        font.setPointSize(12)
        self.lblDuration.setFont(font)
        self.lblDuration.setStyleSheet("color: rgb(108, 216, 255);")
        self.lblDuration.setObjectName("lblDuration")
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate(
            "MainWindow", "Gerador de voz - Eng. Acústica (UFSM)"))
        self.btnSynthesize.setText(_translate("MainWindow", " Gerar \n"
                                              "  voz          "))
        self.btnClear.setText(_translate("MainWindow", "Limpar      "))
        self.lblTitle.setText(_translate(
            "MainWindow", "Transforme seu texto em voz"))
        self.lblEnterTxt.setText(_translate(
            "MainWindow", "Adicione seu texto:"))
        # self.lblStatus.setText(_translate("MainWindow", "Síntese feita com sucesso."))
        # self.lblTime.setText(_translate("MainWindow", "Tempo decorrido: 03 s."))
        self.btnSetup.setText(_translate("MainWindow", "Configurar  "))
        self.lblDuration.setText(_translate("MainWindow", "00:00 / 00:00"))


# %% Class dlgSetup
class guiSetup(object):
    '''
    Classe guiSetup
    Instancia itens gráficos contidos na janela de configurações do app.
    Gerada utilizando o software Qt designer:
        https://build-system.fman.io/qt-designer-download
    '''

    def setupUi(self, guiSetup):
        guiSetup.setObjectName("guiSetup")
        guiSetup.resize(400, 294)
        guiSetup.setWindowIcon(QtGui.QIcon(p+'\\icon_settings_win.ico'))
        guiSetup.setStyleSheet("background-color: rgb(75, 75, 75);")
        self.lblFormat = QtWidgets.QLabel(guiSetup)
        self.lblFormat.setGeometry(QtCore.QRect(10, 202, 91, 16))
        font = QtGui.QFont()
        font.setFamily("Sitka Small")
        font.setPointSize(14)
        self.lblFormat.setFont(font)
        self.lblFormat.setStyleSheet("color: rgb(255, 255, 255);")
        self.lblFormat.setObjectName("lblFormat")
        self.rbtn_wav = QtWidgets.QRadioButton(guiSetup)
        self.rbtn_wav.setGeometry(QtCore.QRect(200, 200, 82, 23))
        font = QtGui.QFont()
        font.setFamily("Sitka Small")
        font.setPointSize(14)
        self.rbtn_wav.setFont(font)
        self.rbtn_wav.setStyleSheet("color: rgb(255, 255, 255);")
        self.rbtn_wav.setObjectName("rbtn_wav")
        self.rbtn_mp3 = QtWidgets.QRadioButton(guiSetup)
        self.rbtn_mp3.setGeometry(QtCore.QRect(110, 200, 82, 23))
        font = QtGui.QFont()
        font.setFamily("Sitka Small")
        font.setPointSize(14)
        self.rbtn_mp3.setFont(font)
        self.rbtn_mp3.setStyleSheet("color: rgb(255, 255, 255);")
        self.rbtn_mp3.setObjectName("rbtn_mp3")
        self.lblDevice = QtWidgets.QLabel(guiSetup)
        self.lblDevice.setGeometry(QtCore.QRect(10, 10, 121, 31))
        font = QtGui.QFont()
        font.setFamily("Sitka Small")
        font.setPointSize(14)
        self.lblDevice.setFont(font)
        self.lblDevice.setStyleSheet("color: rgb(255, 255, 255);")
        self.lblDevice.setObjectName("lblDevice")
        self.lblSampleRate = QtWidgets.QLabel(guiSetup)
        self.lblSampleRate.setGeometry(QtCore.QRect(10, 90, 211, 31))
        font = QtGui.QFont()
        font.setFamily("Sitka Small")
        font.setPointSize(14)
        self.lblSampleRate.setFont(font)
        self.lblSampleRate.setStyleSheet("color: rgb(255, 255, 255);")
        self.lblSampleRate.setObjectName("lblSampleRate")
        self.lblChannels = QtWidgets.QLabel(guiSetup)
        self.lblChannels.setGeometry(QtCore.QRect(10, 144, 81, 31))
        font = QtGui.QFont()
        font.setFamily("Sitka Small")
        font.setPointSize(14)
        self.lblChannels.setFont(font)
        self.lblChannels.setStyleSheet("color: rgb(255, 255, 255);")
        self.lblChannels.setObjectName("lblChannels")
        self.btnSave = QtWidgets.QPushButton(guiSetup)
        self.btnSave.setGeometry(QtCore.QRect(40, 252, 111, 31))
        font = QtGui.QFont()
        font.setFamily("Sitka Small")
        font.setPointSize(14)
        self.btnSave.setFont(font)
        self.btnSave.setStyleSheet("background-color: None;")
        self.btnSave.setObjectName("btnSave")
        self.btnCancel = QtWidgets.QPushButton(guiSetup)
        self.btnCancel.setGeometry(QtCore.QRect(250, 250, 111, 31))
        font = QtGui.QFont()
        font.setFamily("Sitka Small")
        font.setPointSize(14)
        self.btnCancel.setFont(font)
        self.btnCancel.setStyleSheet("background-color: None;")
        self.btnCancel.setObjectName("btnCancel")
        self.scrollArea = QtWidgets.QScrollArea(guiSetup)
        self.scrollArea.setGeometry(QtCore.QRect(90, 140, 311, 41))
        self.scrollArea.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 309, 39))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.frame_listSampleRate = QtWidgets.QFrame(guiSetup)
        self.frame_listSampleRate.setGeometry(QtCore.QRect(230, 87, 171, 41))
        self.frame_listSampleRate.setStyleSheet(
            "background-color: rgb(255, 255, 255);")
        self.frame_listSampleRate.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_listSampleRate.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_listSampleRate.setObjectName("frame_listSampleRate")
        self.listSampleRate = QtWidgets.QComboBox(self.frame_listSampleRate)
        self.listSampleRate.setGeometry(QtCore.QRect(0, 0, 171, 41))
        font = QtGui.QFont()
        font.setFamily("Sitka Small")
        font.setPointSize(12)
        self.listSampleRate.setFont(font)
        self.listSampleRate.setStyleSheet("background-color: None;")
        self.listSampleRate.setObjectName("listSampleRate")
        self.frame_listDevices = QtWidgets.QFrame(guiSetup)
        self.frame_listDevices.setGeometry(QtCore.QRect(0, 40, 400, 41))
        self.frame_listDevices.setStyleSheet(
            "background-color: rgb(255, 255, 255);")
        self.frame_listDevices.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_listDevices.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_listDevices.setObjectName("frame_listDevices")
        self.listDevices = QtWidgets.QComboBox(self.frame_listDevices)
        self.listDevices.setGeometry(QtCore.QRect(0, 0, 400, 41))
        font = QtGui.QFont()
        font.setFamily("Sitka Small")
        font.setPointSize(12)
        self.listDevices.setFont(font)
        self.listDevices.setStyleSheet("background-color: None;")
        self.listDevices.setObjectName("listDevices")
        self.frame_listDevices.raise_()
        self.lblFormat.raise_()
        self.rbtn_wav.raise_()
        self.rbtn_mp3.raise_()
        self.lblDevice.raise_()
        self.lblSampleRate.raise_()
        self.lblChannels.raise_()
        self.btnSave.raise_()
        self.btnCancel.raise_()
        self.scrollArea.raise_()
        self.frame_listSampleRate.raise_()

        self.retranslateUi(guiSetup)
        QtCore.QMetaObject.connectSlotsByName(guiSetup)

    def retranslateUi(self, guiSetup):
        _translate = QtCore.QCoreApplication.translate
        guiSetup.setWindowTitle(_translate("guiSetup", "Configurações"))
        self.lblFormat.setText(_translate("guiSetup", "Formato:"))
        self.rbtn_wav.setText(_translate("guiSetup", "wav"))
        self.rbtn_mp3.setText(_translate("guiSetup", "mp3"))
        self.lblDevice.setText(_translate("guiSetup", "Dispositivo:"))
        self.lblSampleRate.setText(_translate(
            "guiSetup", "Taxa de amostragem:"))
        self.lblChannels.setText(_translate("guiSetup", "Canais:"))
        self.btnSave.setText(_translate("guiSetup", "Salvar"))
        self.btnCancel.setText(_translate("guiSetup", "Cancelar"))

# %% Class appTTS


class appTTS(QtWidgets.QMainWindow, guiMain):
    def __init__(self, parent=None):
        super(appTTS, self).__init__(parent)
        self.setupUi(self)
        # Atualização gráfica
        self.qTimer = QtCore.QTimer()
        self.qTimer.setInterval(125)  # 125 milisegundos
        self.qTimer.timeout.connect(self.update)
        self.qTimer.start()
        # Botão Play
        self.mixerInit = False
        self.btnPlay.setEnabled(False)
        self.btnPlay.clicked.connect(self.btnPlay_Action)
        self.btnPlay.setStyleSheet("background-color: rgb(75, 75, 75);")
        # Botão Pause
        self.btnPause.setEnabled(False)
        self.btnPause.clicked.connect(self.btnPause_Action)
        self.btnPause.setStyleSheet("background-color: rgb(75, 75, 75);")
        self.pause = True
        # Botão Stop
        self.btnStop.setEnabled(False)
        self.btnStop.clicked.connect(self.btnStop_Action)
        self.btnStop.setStyleSheet("background-color: rgb(75, 75, 75);")
        # Botão Clear
        self.btnClear.setEnabled(True)
        self.btnClear.clicked.connect(self.btnClear_Action)
        # Botão Synthesize
        self.btnSynthesize.setEnabled(False)
        self.btnSynthesize.clicked.connect(self.btnSynthesize_Action)
        self.SynthesizedText = ''
        # Botão Configurações
        self.btnSetup.setEnabled(True)
        self.btnSetup.clicked.connect(self.btnSetup_Action)
        # Gerador de índice
        self.generator = (os.getcwd() + '\\audio_%03i.mp3' %
                          i for i in count(1))
        # Iniciando dispositivo de áudio
        self.dev, self.devDefault, self.infosDev, self.sampleDefault,\
            self.numChannels, self.outChannels, self.audioFormat, self.sd_device = init_device()
        self.current_SampleRate = self.sampleDefault
        # Áudio sintetizado
        self.audioData = None
        # stream de áudio
        self.stream = None
        self.elapsed_time = str(0)
        # Barra de progresso
        self.progressBar.setEnabled(False)
        self.progressBar.sliderPressed.connect(self.pressed_progressBar)
        self.progressBar.sliderReleased.connect(self.released_progressBar)
        self.lblDuration.setText("00:00 / 00:00")

    def update(self):
        '''
        Função de atualização dos elementos gráficos de acordo com as alterações
        feitas pelo usuário nos parâmetros contigos na janela principal.
        '''
        try:
            if self.textEntry.toPlainText() == ''\
                    or self.textEntry.toPlainText() == self.SynthesizedText:
                self.btnSynthesize.setEnabled(False)
                if self.SynthesizedText == '':
                    self.progressBar.setEnabled(False)
                    self.progressBar.setValue(0)
                elif self.textEntry.toPlainText() == '':
                    self.btnPlay.setEnabled(False)
                    self.progressBar.setEnabled(False)
                else:
                    self.progressBar.setEnabled(False)
            else:
                self.btnPlay.setEnabled(False)
                self.btnPlay.setStyleSheet(
                    "background-color: rgb(75, 75, 75);")
                self.lblDuration.setText("00:00 / 00:00")
                self.btnSynthesize.setEnabled(True)
                self.lblStatus.setText('')
                self.lblTime.setText('')
                self.progressBar.setEnabled(False)
                self.progressBar.setValue(0)

            if self.textEntry.toPlainText() != ''\
                    and self.textEntry.toPlainText() == self.SynthesizedText:
                if self.btnSynthesize.isEnabled() == False:
                    self.btnPlay.setEnabled(True)
                    self.btnPlay.setStyleSheet(
                        "background-color: rgb(128, 255, 171);")
                    self.lblStatus.setText("Síntese feita com sucesso.")
                    self.lblTime.setText(
                        "Tempo decorrido: " + str(rd(self.elapsed_time)).replace(".", ",") + " s.")
                    self.lblDuration.setText(
                        ' 00:00 / ' + f'{self.min:02d}:{self.sec:02d}')
                else:
                    pass
            else:
                self.lblDuration.setText("00:00 / 00:00")

            if not self.stream is None:
                if self.stream.streamData.active:
                    self.btnPlay.setStyleSheet(
                        "background-color: rgb(75, 75, 75);")
                    if self.stream.isPause:
                        pass
                    else:
                        if (self.stream.framesRead + self.stream.frame) >= self.progressBar.maximum():
                            self.progressBar.setValue(0)
                            self.btnPlay.setStyleSheet(
                                "background-color: rgb(128, 255, 171);")
                            self.btnPause.setStyleSheet(
                                "background-color: rgb(75, 75, 75);")
                            self.btnStop.setStyleSheet(
                                "background-color: rgb(75, 75, 75);")
                        else:
                            self.progressBar.setValue(self.stream.framesRead)
                            self.infosDuration()
                            self.btnPlay.setEnabled(False)

                else:
                    if self.textEntry.toPlainText() != self.SynthesizedText\
                            or self.textEntry.toPlainText() == '':
                        self.lblDuration.setText("00:00 / 00:00")
                        self.btnPlay.setEnabled(False)
                    else:
                        self.btnPlay.setEnabled(True)
                        self.btnPlay.setStyleSheet(
                            "background-color: rgb(128, 255, 171);")
                        self.lblDuration.setText(
                            ' 00:00 / ' + f'{self.min:02d}:{self.sec:02d}')
                    self.btnPause.setEnabled(False)
                    self.btnStop.setEnabled(False)
            else:
                pass
        except Exception as E:
            print("appTTS.update(): ", E, "\n")

    def pressed_progressBar(self):
        '''
        Função chamada ao detectar o sinal de que o usuário pressionou o "botão"
        da barra de progresso.
        Coloca a strem em modo stand-by até que o usuário solte o "botão".
        '''
        try:
            if self.progressBar.isEnabled():
                self.stream.isPause = True
            else:
                pass
            return
        except Exception as E:
            print("appTTS.pressed_progressBar(): ", E, "\n")

    def released_progressBar(self):
        '''
        Função chama ao detectar o sinal de que o usuário soltou o "botão" da
        barra de progresso.
        Verifica se se a stream está ativa e pega a posição em que a barra se
        encontra para configurar o ponto do áudio em que a reprodução retornará.
        '''
        try:
            if self.progressBar.isEnabled():
                if self.stream.streamData.active:
                    self.stream.framesRead = self.progressBar.value()
                    self.stream.isPause = False
                else:
                    self.stream.framesRead = self.progressBar.value()
                    self.stream.isPause = False
                    self.btnPlay_Action()
            else:
                pass
            return
        except Exception as E:
            print("appTTS.released_progressBar(): ", E, "\n")

    def infosDuration(self):
        '''
        Função que insere o tempo de execução do áudio na label 'lblDuration'
        '''
        try:
            # tempo decorrido da stream de áudio
            _min, _sec = divmod(
                int(self.stream.framesRead/self.sampleDefault), 60)
            self.lblDuration.setText(
                f'{_min:02d}:{_sec:02d}' + ' / ' + f'{self.min:02d}:{self.sec:02d}')
        except Exception as E:
            print("appTTS.infosDuration(): ", E, "\n")

    def btnClear_Action(self):
        '''
        Ação 'Limpar'.
        Encerra a stream e limpa o campo de texto digitado pelo usuário.
        '''
        try:
            if not self.stream is None:
                if self.stream.streamData.active:
                    self.stream.stop()
                    self.stream = None
                else:
                    self.stream = None
            else:
                pass
            self.progressBar.setValue(0)
            self.textEntry.setText('')
            self.lblStatus.setText('')
            self.lblTime.setText('')
            self.SynthesizedText = ''
            self.btnSynthesize.setEnabled(False)
            self.btnPlay.setEnabled(False)
            self.btnPause.setEnabled(False)
            self.btnStop.setEnabled(False)
            self.progressBar.setEnabled(False)
            self.lblDuration.setText("00:00 / 00:00")
            self.btnPlay.setStyleSheet("background-color: rgb(75, 75, 75);")
            self.btnPause.setStyleSheet("background-color: rgb(75, 75, 75);")
            self.btnPause.setIcon(QtGui.QIcon(p+'\\icon_pause.ico'))
            self.btnStop.setStyleSheet("background-color: rgb(75, 75, 75);")
        except Exception as E:
            print("appTTS.btnClear_Action(): ", E, "\n")

    def btnSynthesize_Action(self):
        ''' 
        Ação 'Gerar voz' 
        '''
        try:
            # Ativa o gerador de nome de arquivo
            self.tts_path = next(self.generator)
            self.SynthesizedText = self.textEntry.toPlainText()
            self.TTS(text=self.SynthesizedText,
                     file=self.tts_path,
                     samplerate=self.sampleDefault,
                     audioFormat=self.audioFormat)
        except Exception as E:
            print("appTTS.btnSynthesize_Action(): ", E, "\n")

    def btnPlay_Action(self):
        ''' 
        Ação 'Play'.
        Cria um objeto da Stream e reproduz o áudio sintetizado.
        '''
        try:
            # instanciando a stream sounddevice
            self.stream = stream(device=self.sd_device,
                                 channels=self.outChannels,
                                 numChannels=self.numChannels,
                                 sampleRate=self.sampleDefault,
                                 audioData=self.audioData)
            # Bloqueio botão Play
            self.btnPlay.setEnabled(False)
            self.btnPlay.setStyleSheet("background-color: rgb(75, 75, 75);")
            # Libero botão pause
            self.btnPause.setEnabled(True)
            self.btnPause.setStyleSheet(
                "background-color: rgb(255, 251, 124);")
            # Libero botão stop
            self.btnStop.setEnabled(True)
            self.btnStop.setStyleSheet("background-color: rgb(255, 99, 101);")
            # dando início a stream
            self.stream.start()
            # Libero a barra de progresso
            self.progressBar.setEnabled(True)
            # Setando mínino da barra de progresso
            self.progressBar.setMinimum(0)
            # Setando máximo da barra de progresso
            self.progressBar.setMaximum(self.stream.numSamples)
            # Setando passo de contagem da barra
            self.progressBar.setSingleStep(self.stream.frame)
        except Exception as E:
            print("appTTS.btnPlay_Action(): ", E, "\n")

    def btnPause_Action(self):
        ''' 
        Ação 'Pause'.
            'pause' = True: Mantem a reprodução do áudio em modo stand-by pelo
            método stream.pause()
            'pause' = False: Mantém a reprodução do áudio normalmente.

        '''
        try:
            if self.pause:
                self.stream.pause()
                self.btnPause.setIcon(QtGui.QIcon(p+'\\icon_unpause.ico'))
                self.btnPause.setIconSize(QtCore.QSize(75, 75))
            else:
                self.stream.pause()
                self.btnPause.setIcon(QtGui.QIcon(p+'\\icon_pause.ico'))
            self.pause = not self.pause
        except Exception as E:
            print("appTTS.btnPause_Action(): ", E, "\n")

    def btnStop_Action(self):
        '''
        Ação 'Stop'.
        Encerra a reprodução do áudio pelo método strem.stop().
        '''
        try:
            if not self.stream is None:
                if self.stream.streamData.active:
                    self.stream.stop()
                else:
                    pass
            else:
                pass
            self.pause = True
            self.progressBar.setValue(0)
            self.btnPause.setIcon(QtGui.QIcon(p+'\\icon_pause.ico'))
            self.btnPlay.setEnabled(True)
            self.btnPlay.setStyleSheet("background-color: rgb(128, 255, 171);")
            self.btnPause.setEnabled(False)
            self.btnPause.setStyleSheet("background-color: rgb(75, 75, 75);")
            self.btnStop.setEnabled(False)
            self.btnStop.setStyleSheet("background-color: rgb(75, 75, 75);")
        except Exception as E:
            print("appTTS.btnStop_Action(): ", E, "\n")

    def btnSetup_Action(self):
        '''
        Ação 'Setup'.
        Abre a janela de configurações, que ao ser fechada coleta as alterações
        feitas pelo usuário.
        '''
        try:
            self.btnStop_Action()
            self.btnPlay.setEnabled(False)
            self.qTimer.stop()
            self.btnPlay.setStyleSheet("background-color: rgb(75, 75, 75);")
            self.btnPause.setStyleSheet("background-color: rgb(75, 75, 75);")
            self.btnStop.setStyleSheet("background-color: rgb(75, 75, 75);")
            settings = setSetup(self.dev, self.devDefault, self.infosDev, self.sampleDefault,
                                self.numChannels, self.outChannels, self.audioFormat, self.sd_device)
            settings.exec_()

            if settings.finished:
                self.dev = settings.dev
                self.devDefault = settings.devDefault
                self.infosDev = settings.infosDev
                self.sampleDefault = settings.sampleDefault
                self.numChannels = settings.numChannels
                self.outChannels = settings.outChannels
                self.audioFormat = settings.audioFormat
                self.sd_device = settings.sd_device
                if settings.changed:
                    if self.textEntry.toPlainText() != ''\
                            and self.textEntry.toPlainText() == self.SynthesizedText:
                        self.btnSynthesize_Action()
                    else:
                        pass
                else:
                    if self.textEntry.toPlainText() == self.SynthesizedText\
                            and self.textEntry.toPlainText() != '':
                        self.btnPlay.setEnabled(True)
                        self.btnPlay.setStyleSheet(
                            "background-color: rgb(128, 255, 171);")
                self.qTimer.start()
                self.btnPlay.setEnabled(True)
        except Exception as E:
            print("appTTS.btnSetup_Action(): ", E, "\n")

    def TTS(self, text: str, file: str, samplerate: int, audioFormat: str):
        '''
        Função que recebe um texto, sintetiza e por fim gera um arquivo de áudio 
        gerado por gtts.gTTs.save(). Abre o arquivo usando o módulo librosa.load()
        e verifica a compatibilidade de taxa de amostragem e formato de áudio:
            -> caso a taxa de amostragem seja diferente da padrão de 24kHz ou 22,05kHz,
               reamostra o sinal pelo método librosa.resample()
            -> caso o formato de áudio seja diferente do padrão '.mp3', exclui salva como
               arquivo '.wav' e deleta o arquivo '.mp3' antigo.
        Parameters
        ----------
        text : str
            texto a ser sintetizado pela biblioteca gtts.gTTs()
        file : str
            mesmo nome do arquivo salvo pelo método gtts.gTTs.save().
        samplerate : int
            taxa de amostragem do dispositivo de áudio utilizado.
        audioFormat : str
            formato do arquivo de áudio (.mp3 ou .wav).

        Returns
        -------
        numpy.array contendo o sinal de áudio e taxa de amostragem corretamente
        ajustados para serem utilizados pelo sounddevice.

        '''
        try:
            # Limpando Labels
            self.lblStatus.setText('')
            self.lblTime.setText('')

            # Inicia contagem de tempo decorrido
            self.start_time = time.time()

            # Fornece texto ao gtts
            tts = gTTS(text=text, lang='pt-br')
            # Salva o arquivo .mp3
            tts.save(self.tts_path)  # NoT a file-like object

            if audioFormat != 'mp3':
                data, fs = librosa.load(self.tts_path)
                librosa.output.write_wav(
                    self.tts_path.replace("mp3", "wav"), data, 24000)
                data, fs = librosa.load(self.tts_path.replace("mp3", "wav"))
                os.remove(self.tts_path)
            else:
                print(self.tts_path)
                data, fs = librosa.load(self.tts_path)
                
            # if self.current_SampleRate != self.sampleDefault:
            if self.sampleDefault != 24000 or self.sampleDefault != 22500:
                data = librosa.resample(data, 24000, self.sampleDefault)
                # print('\nResample de ', self.current_SampleRate, 'Hz para ', self.sampleDefault, ' Hz.\n')
                self.current_SampleRate = self.sampleDefault

            self.audioData = data

            # fim do tempo decorrido
            self.elapsed_time = time.time() - self.start_time

            # Libera botão play
            self.btnPlay.setEnabled(True)
            self.btnPlay.setStyleSheet("background-color: rgb(128, 255, 171);")

            # Settando Labels
            self.lblStatus.setText("Síntese feita com sucesso.")
            self.lblTime.setText(
                "Tempo decorrido: " + str(rd(self.elapsed_time)).replace(".", ",") + " s.")

            # duração total da medição
            self.min, self.sec = divmod(
                int(self.audioData.size/self.sampleDefault), 60)
            self.lblDuration.setText(
                ' 00:00 / ' + f'{self.min:02d}:{self.sec:02d}')

        except Exception as E:
            print("appTTS.TTS(): ", E, "\n")


# %% Class stream
class stream(object):
    def __init__(self, device, channels, numChannels, sampleRate, audioData):
        self.device = device
        self.outChannels = channels
        self.numChannels = numChannels
        self.sampleRate = sampleRate
        self.audioData = audioData
        self.isPause = False
        self.framesRead = 0
        self.numSamples = self.audioData.size
        self.frame = 512
        self.q = Queue()
        self.streamData = sd.OutputStream(samplerate=self.sampleRate,
                                          blocksize=self.frame,
                                          device=self.device,
                                          channels=self.numChannels,
                                          dtype='float32',
                                          callback=self.callback)

    def start(self):
        '''
        Função de início da stream.
        Chama o método sounddevice.OutputStream.start e inicia o fluxo de áudio.
        '''
        if self.streamData.active:
            pass
        else:
            self.framesRead = self.framesRead
            self.streamData.start()
        return

    def pause(self):
        '''
        Função de pausa da stream.
            'isPause' = True: na chamada de retorno ('callback') a variável de
        saída de áudio 'outdata' receberá valor nulo. Deixando de enviar os
        frames do vetor de áudio ('audioData') para o dispositivo de áudio.
            'isPause' = False: a chamada de retorno ('callback') seguira normal-
        mente enviando os frames do vetor de áudio ('audioData') para o disposi-
        tivo de áudio.

        '''
        self.isPause = not self.isPause
        return

    def stop(self):
        '''
        Função de parada da strem.
        Encerra o fluxo de áudio e deixa de chamar a função 'callback'.
        '''
        if self.streamData.active:
            self.streamData.stop()
        else:
            pass
        return

    def callback(self, outdata: ndarray, frames: int,
                 times: type, status: sd.CallbackFlags):
        '''
        Função de retorno de chamada padronizada. Para maiores informações leia
        a documentação em sounddevice.OutputStream.

        Parameters
        ----------
        outdata : ndarray
            Vetor com os frames a serem executados a cada chamada da função.
        frames : int
            Tamanho do bloco de dados a ser executado em cada iteração.
        times : type
            Tempo atual do fluxo em segundos, para maiores informações leia a
            documentação em sounddevice.Stream.
        status : sd.CallbackFlags
            Variável com sinalizadores de status da chamada de retorno, para maiores
            informações leia a documentação em sounddevice.CallbackFlags.

        Returns
        -------
        None.

        '''
        try:
            if self.isPause:
                outdata[:] = 0
            else:
                if self.audioData.any() or not self.audioData is None:
                    for i in range(len(self.outChannels)):
                        outdata[:, i] = self.audioData[self.framesRead: self.framesRead + self.frame]
                    self.framesRead += self.frame
                    self.countDn = self.numSamples - self.framesRead
                    self.q.put_nowait(self.framesRead)
                    if self.framesRead >= self.numSamples or self.countDn < self.frame:
                        self.stop()

                else:
                    pass
        except Exception as E:
            print("Stream.callback(): ", E, "\n")
        return


# %% Class setSetup
class setSetup(QtWidgets.QDialog, guiSetup):
    '''
    Classe setSetup, criada para instânciar a interface gráfica guiSetup,
    onde os parâmetros de entrada do App são alterados pelo usuário.
    '''

    def __init__(self, dev, devDefault, infosDev, sampleDefault, numChannels,
                 outChannels, audioFormat, sd_device):
        super(setSetup, self).__init__(None)
        self.setupUi(self)
        self.finished = False
        self.dev = dev
        self.devDefault = devDefault
        self.infosDev = infosDev
        self.sampleDefault = sampleDefault
        self.numChannels = numChannels
        self.outChannels = outChannels
        self.audioFormat = audioFormat
        self.sd_device = sd_device
        # Ação do botão Cancelar
        self.btnCancel.clicked.connect(self.btnCancel_Action)
        # Ação do botão Salvar
        self.btnSave.clicked.connect(self.btnSave_Action)
        self.btnSave.setEnabled(False)
        # Inserindo a lista de dispositivos na GUI, adicionando itens no combobox
        for i in range(len(self.dev['out'])):
            self.listDevices.addItem("")
            self.listDevices.setItemText(i, self.dev['out'][i]['name'])
        # Setando canais de saída do dispotivo de áudio padrão
        self._lisOutChannels(self.devDefault)
        # Inserindo lista de taxa de amostragem para o dispositivo selecionadO
        self._listSampleRate(self.devDefault)
        # Setando dispositivo padrão na GUI
        self.listDevices.setCurrentIndex(self.devDefault)
        # Iniciando loop de atualização da GUI
        self.qTimer = QtCore.QTimer()
        self.qTimer.setInterval(125)  # 125 milisegundos
        self.qTimer.timeout.connect(self.update)
        self.qTimer.start()
        # Salvando variáveis para detectar alterações feitas pelos usuários
        self.setDevice = self.listDevices.currentIndex()
        self.setSampleRate = self.infosDev['sampleRate'][self.listSampleRate.currentIndex(
        )]
        # Setando formato de áudio MP3
        if self.audioFormat == 'mp3':
            self.rbtn_mp3.setChecked(True)
            self.setaudioFormat = 'mp3'
        else:
            self.rbtn_wav.setChecked(True)
            self.setaudioFormat = 'wav'
        self.rbtn_mp3.clicked.connect(self.rbtn_mp3_Action)
        self.rbtn_wav.clicked.connect(self.rbtn_wav_Action)
        # Variáveis para detectar alterações
        self.deviceChanged = False
        self.samplerateChanged = False
        self.formatChanged = False
        self.channelChanged = False
        self.changed = self.getChangeds()

    def update(self):
        '''
        Função de atualização dos elementos gráficos de acordo com as alterações
        feitas pelo usuário nos parâmetros contigos na janela de configurações.
        '''
        try:
            # A cada iteração recolhe os canais ativos para verificação de alterações
            self.checkCh = self.getChannels()

            # Verifica se o dispositivo de áudio selecionado é o mesmo que o definido anteriormente.
            if self.listDevices.currentIndex() != self.setDevice\
                    or self.dev['out'][self.setDevice]['name'] != self.dev['out'][self.listDevices.currentIndex()]['name']:
                self._listSampleRate(self.listDevices.currentIndex())
                self._lisOutChannels(self.listDevices.currentIndex())
                self.setDevice = self.listDevices.currentIndex()
                if self.setDevice != self.devDefault:
                    self.btnSave.setEnabled(True)
                    self.deviceChanged = True
                else:
                    self.deviceChanged = False
                    if self.getChangeds():
                        pass
                    else:
                        self.btnSave.setEnabled(False)

            # Verifica se a taxa de amostragem selecionada é a mesma que a definida anteriomente
            elif self.setSampleRate != self.infosDev['sampleRate'][self.listSampleRate.currentIndex()]:
                self.setSampleRate = self.infosDev['sampleRate'][self.listSampleRate.currentIndex(
                )]
                if self.setSampleRate != self.sampleDefault:
                    self.btnSave.setEnabled(True)
                    self.samplerateChanged = True
                else:
                    self.samplerateChanged = False
                    if self.getChangeds():
                        pass
                    else:
                        self.btnSave.setEnabled(False)

            # Verifica se o formato de áudio é o mesmo que o definido anteriomente
            elif self.formatChanged:
                if self.rbtn_mp3.isChecked():
                    if self.audioFormat == 'mp3':
                        self.formatChanged = False
                        if self.getChangeds():
                            pass
                        else:
                            self.btnSave.setEnabled(False)
                    else:
                        self.btnSave.setEnabled(True)
                else:
                    if self.audioFormat == 'wav':
                        self.formatChanged = False
                        if self.getChangeds():
                            pass
                        else:
                            self.btnSave.setEnabled(False)
                    else:
                        self.btnSave.setEnabled(True)

            # Verifica se os canais de saída de aúdio ativos são os mesmo definidos anteriomente
            elif len(self.setoutChannels) != len(self.checkCh):
                self.setoutChannels = self.getChannels()
                if len(self.setoutChannels) == len(self.outChannels):
                    if self.setoutChannels == self.outChannels:
                        self.channelChanged = False
                        if self.getChangeds():
                            pass
                        else:
                            self.btnSave.setEnabled(False)
                    else:
                        self.channelChanged = True
                        self.btnSave.setEnabled(True)
                else:
                    self.channelChanged = True
                    self.btnSave.setEnabled(True)

            else:
                pass

        except Exception as E:
            print("setSetup.update(): ", E, "\n")

    def rbtn_mp3_Action(self):
        ''''
        Ação radio button 'mp3'
        '''
        self.formatChanged = True

    def rbtn_wav_Action(self):
        ''''
        Ação radio button 'wav'
        '''
        self.formatChanged = True

    def btnSave_Action(self):
        '''
        Ação 'Salvar'
        Coleta as informações do dispositivo de áudio e envia para a classe appTTS
        e fecha a janela de configurações.
        '''
        try:
            self.changed = self.getChangeds()
            self.devDefault = self.listDevices.currentIndex()
            self.infosDev = getInfosDevice(self.devDefault)
            self.sampleDefault = self.infosDev['sampleRate'][self.listSampleRate.currentIndex(
            )]
            self.outChannels = self.getChannels()
            global sd_device
            self.sd_device = trueDevice(self.dev['inDefault'], self.devDefault)
            if self.rbtn_mp3.isChecked():
                self.audioFormat = 'mp3'
            else:
                self.audioFormat = 'wav'
            self.finished = True
            self.close()

        except Exception as E:
            print("setSetup.btnSave_Action(): ", E, "\n")

    def btnCancel_Action(self):
        '''
        Ação 'Cancelar'
        Fecha a janela de configurações sem salvar as possíveis alterações feitas
        pelo usuário nos parâmetros.
        '''
        try:
            self.finished = True
            self.close()
            return
        except Exception as E:
            print("setSetup.btnCancel_Action(): ", E, "\n")

    def _lisOutChannels(self, device):
        '''
        Função que lista os canais de saída do dispositivo de áudio na janela
        de configurações na forma de QCheckBox -> PyQt5.QtWidgets.QCheckBox.

        Parameters
        ----------
        device : int
            Número do dispositivo de saída de áudio obtido pela função
            query_devices():
                dev = query_devices()
                device = dev['outDefault'].

        Returns
        -------
        -> Lista de canais adicionados na interface gráfica em forma de QCheckBox
           com ao menos os dois primeiros canais ativados.
        -> self.setoutChannels: vetor com os números dos canais ativados.
        '''
        try:
            _infosDev = getInfosDevice(device)
            numChannels = self.dev['out'][device]['max_output_channels']
            self.widget = QtWidgets.QWidget()
            self.hbox = QtWidgets.QHBoxLayout()

            self.listCheckBox = []
            # for i in range(len(_infosDev['outChannels'])):
            # self.listCheckBox.append(str(_infosDev['outChannels'][i]))
            for i in range(numChannels):
                self.listCheckBox.append(str(i+1))

            for i, j in enumerate(self.listCheckBox):
                self.listCheckBox[i] = QtWidgets.QCheckBox(j)
                self.hbox.addWidget(self.listCheckBox[i])
                if (i+1) in self.outChannels:
                    self.listCheckBox[i].setCheckState(QtCore.Qt.Checked)
                elif i == 0 or i == 1:
                    self.listCheckBox[i].setCheckState(QtCore.Qt.Checked)

            self.widget.setLayout(self.hbox)
            self.scrollArea.setWidget(self.widget)
            self.scrollArea.setAlignment(QtCore.Qt.AlignCenter)
            self.setoutChannels = self.getChannels()
            self.checkCh = self.setoutChannels
            return
        except Exception as E:
            print("setSetup._lisOutChannels(): ", E, "\n")

    def getChannels(self):
        '''
        Função que retorna em um vetor os números dos canais ativados.

        Returns
        -------
        _outChannels : int array
            Vetor com os números dos canais cujos QCheckBox estão selecionados
            (QtWidgets.QCheckBox.checkState() == True).

        '''
        try:
            stateChannels = []
            for i, v in enumerate(self.listCheckBox):
                stateChannels.append(v.checkState())

            _outChannels = []

            for i in range(len(stateChannels)):
                if stateChannels[i]:
                    ch = i + 1
                    _outChannels.append(ch)
                else:
                    pass
            return _outChannels
        except Exception as E:
            print("setSetup.getChannels(): ", E, "\n")

    def _listSampleRate(self, device):
        '''
        Função que adiciona na interface gráfica as taxas de amostragem
        suportadas pelo dispositivo de saída de áudio.

        Parameters
        ----------
        device : int
            Número do dispositivo de saída de áudio obtido pela função
            query_devices():
                dev = query_devices()
                device = dev['outDefault'].

        Returns
        -------
        Lista de taxas de amostragem suportadas pelo dispositivo de saída de
        áudio em forma de itens no QComboBox (PyQt5.QtWidgets.QComboBox).

        '''
        try:
            _infosDev = getInfosDevice(device)
            for i in range(len(_infosDev['sampleRate'])):
                self.listSampleRate.addItem("")
                self.listSampleRate.setItemText(
                    i, str(_infosDev['sampleRate'][i]/1000).replace(".", ",") + " kHz")
            # Setando taxa de amostragem em 24kHz ou a padrão
            if self.sampleDefault in _infosDev['sampleRate']:
                self.listSampleRate.setCurrentIndex(
                    _infosDev['sampleRate'].index(self.sampleDefault))
            elif 24000 in _infosDev['sampleRate']:
                self.listSampleRate.setCurrentIndex(
                    _infosDev['sampleRate'].index(24000))
            elif 44100 in _infosDev['sampleRate']:
                self.listSampleRate.setCurrentIndex(
                    _infosDev['sampleRate'].index(44100))
            elif 48000 in _infosDev['sampleRate']:
                self.listSampleRate.setCurrentIndex(
                    _infosDev['sampleRate'].index(48000))
            else:
                self.listSampleRate.setCurrentIndex(
                    len(_infosDev['sampleRate']))
            return
        except Exception as E:
            print("setSetup._listSampleRate(): ", E, "\n")

    def getChangeds(self):
        '''
        Função que verifica se houve alterações no parâmetros do dispositivo.

        Returns
        -------
        changed : boolean
            True: se houve alguma alteração.
            False: se não houve alterações
        '''

        try:
            if self.deviceChanged == False\
                    and self.samplerateChanged == False\
                    and self.formatChanged == False\
                    and self.channelChanged == False:
                changed = False
            else:
                changed = True
            return changed
        except Exception as E:
            print("setSetup.getChangeds(): ", E, "\n")


# %% Executar apenas se este arquivo.py for __main__
if __name__ == "__main__":
    import sys
    if sys.platform == 'win32' or sys.platform == 'win64':
        import ctypes
        myappid = u'mycompany.myproduct.subproduct.version'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    else:
        pass
    app = QtWidgets.QApplication(sys.argv)
    startApp = appTTS()
    startApp.show()
    app.exec_()
