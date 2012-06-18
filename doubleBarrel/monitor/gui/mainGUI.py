'''
Created on 2012-06-15

@author: Mat
'''

import sys
from ui import mainUI
from PyQt4 import QtGui, QtCore
from functools import partial


class MainGUI(QtGui.QMainWindow, mainUI.Ui_mainUi):

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setupUi(self)
        self._extraUiSetup()
        self._setupCallbacks()
        self._setDefaults()

    def _extraUiSetup(self):
        '''
        Does any remaining setup that cannot be done from within the designer.
        '''

        # Group the actions for changing the split orientation.
        self.orientSplitActionGroup = QtGui.QActionGroup(self.menuManage)
        self.horizontalSplitAction.setActionGroup(self.orientSplitActionGroup)
        self.verticalSplitAction.setActionGroup(self.orientSplitActionGroup)

        # Group the actions for showing/hiding the log.
        self.showLogActionGroup = QtGui.QActionGroup(self.menuLog)
        self.showLogAction.setActionGroup(self.showLogActionGroup)
        self.hideLogAction.setActionGroup(self.showLogActionGroup)

        # Group the actions for display mode.
        self.displayModeActionGroup = QtGui.QActionGroup(self.menuPreferences)
        self.simpleModeAction.setActionGroup(self.displayModeActionGroup)
        self.advancedModeAction.setActionGroup(self.displayModeActionGroup)

    def _setupCallbacks(self):
        '''
        Sets up the signal/slot connections for the GUI.
        '''

        # Manage the log display changing from toggling the checkbox.
        self.showLogCheck.stateChanged.connect(self._setLogVis)

        # Manage the log display changing from moving the splitter.
        self.logSplitter.splitterMoved.connect(self._setLogChecks)

        # Connect the log checkbox to the icon.
        self.showLogCheck.stateChanged.connect(self.showLogLabel.setEnabled)

        # Connections for log splitter orientation menu items.
        self.horizontalSplitAction.triggered.connect(partial(self._setLogSplitOrient, QtCore.Qt.Horizontal))
        self.verticalSplitAction.triggered.connect(partial(self._setLogSplitOrient, QtCore.Qt.Vertical))

        # Connections for log visibility menu items.
        self.showLogAction.triggered.connect(partial(self._setLogVis, 1))
        self.hideLogAction.triggered.connect(partial(self._setLogVis, 0))

    def _setDefaults(self):
        '''
        Set the default state of the GUI.
        '''

        # Ensure the log is displayed properly.
        self.showLogCheck.stateChanged.emit(self.showLogCheck.checkState())

    def _setLogSplitOrient(self, orientation):
        '''
        Sets the orientation of the log splitter.
        '''

        self.logSplitter.setOrientation(orientation)

    def _setLogChecks(self):
        '''
        Sets the state of the checkbox based on whether the log is showing.
        '''

        logState = self.isLogShowing()

        self.showLogCheck.blockSignals(True)
        self.showLogCheck.setCheckState(logState)
        self.showLogCheck.blockSignals(False)

        self.showLogAction.blockSignals(True)
        self.showLogAction.setChecked(logState)
        self.showLogAction.blockSignals(False)

        self.hideLogAction.blockSignals(True)
        self.hideLogAction.setChecked(not logState)
        self.hideLogAction.blockSignals(False)

        self.showLogLabel.setEnabled(logState)

    @QtCore.pyqtSlot(int)
    def _setLogVis(self, state):
        '''
        Sets the visibility of the log display area.
        '''

        self.logSplitter.setSizes([1, state])
        self._setLogChecks()

    def isLogShowing(self):
        '''
        Returns whether the log is showing.
        '''

        return self.logSplitter.sizes()[-1]


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    mainGUI = MainGUI()
    mainGUI.show()
    sys.exit(app.exec_())
