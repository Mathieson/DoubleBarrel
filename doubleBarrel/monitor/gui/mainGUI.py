'''
Created on 2012-06-15

@author: Mat
'''

import sys
import os
from ui import mainUI
from PyQt4 import QtGui, QtCore
from functools import partial
from monitor.manager import ServerManager


class MainGUI(QtGui.QMainWindow, mainUI.Ui_mainUi):

    def __init__(self, manager=None):
        QtGui.QMainWindow.__init__(self)
        self.setupUi(self)

        self._manager = manager or ServerManager()
        self._servers = {}  # Stores the QTreeWidget as the key and the server as the value.
        self._urls = {}  # Stores the url as the key and the QTreeWidget as the value.

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

        # Set the server tree's columns to be resizeable and fixed (column 1 and 2 respectively)
        self.serverTree.header().setResizeMode(0, QtGui.QHeaderView.Stretch)
        self.serverTree.header().setResizeMode(1, QtGui.QHeaderView.Fixed)

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

        # Connections for the add server buttons.
        self.addButton.clicked.connect(self.addServerBtnPressed)
        self.addServerAction.triggered.connect(self.addServerBtnPressed)

        # Connections for the remove server buttons.
        self.removeButton.clicked.connect(self.removeServerBtnPressed)
        self.removeServerAction.triggered.connect(self.removeServerBtnPressed)

    def _setDefaults(self):
        '''
        Set the default state of the GUI.
        '''

        # Ensure the log is displayed properly.
        self.showLogCheck.stateChanged.emit(self.showLogCheck.checkState())

        # Add all of the servers from the manager.
        for server in self._manager.servers():
            self._addServerToTree(server)

        # Expand all urlGroups by default.
        for urlGroup in self._urls.values():
            urlGroup.setExpanded(True)

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

    def selectedServers(self):
        '''
        Returns the currently selected servers in the tree.
        '''

        selectedItems = self.serverTree.selectedItems()
        selectedServers = []
        for item in selectedItems:
            server = self._servers.get(item)
            if server:
                selectedServers.append(server)

        return selectedServers

    def _addUrlGroupToTree(self, url):
        '''
        Adds a URL group to the tree view that the servers can then be added to.
        '''

        urlGroup = QtGui.QTreeWidgetItem(self.serverTree, [url])
        serverIcon = QtGui.QIcon(os.path.abspath(r'icons\server.png'))
        urlGroup.setIcon(0, serverIcon)
        # Add the urlGroup to the storage dict and then return the control.
        self._urls[url] = urlGroup
        return urlGroup

    def _addServerToTree(self, server):
        '''
        Adds a server to the tree view. This is separated from the addServerBtnPressed function because it needs to get
        called when the GUI is first initialized.
        '''

        sgObj = server.shotgunObject()

        # Get the serverUrl's tree item and add the server under the URL group.
        serverUrl = sgObj.config.server
        urlGroup = self._urls.get(serverUrl)
        if not urlGroup:
            urlGroup = self._addUrlGroupToTree(serverUrl)

        # Add the serverItem to the urlGroup and to the storage dict.
        scriptName = sgObj.config.script_name
        serverItem = QtGui.QTreeWidgetItem(urlGroup, [scriptName])
        self._servers[serverItem] = server

        return serverItem

    def addServerBtnPressed(self):
        '''
        Triggered when one of the add server buttons is pressed.
        '''
        # Bring up a file dialog to allow the user to select an sg file.
        # Call the manager's addServer function, passing it the sg file.
        pass

    def removeServerBtnPressed(self):
        '''
        Triggered when one of the remove server buttons is pressed.
        '''

        selectedItems = self.serverTree.selectedItems()
        for serverItem in selectedItems:
            server = self._servers.get(serverItem)
            # Check to make sure the selected item is a server item and not a urlGroup. We only want to remove servers.
            if server:
                self.serverTree.removeItemWidget(serverItem)
                self._manager.removeServer(server)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    mainGUI = MainGUI()
    mainGUI.show()
    sys.exit(app.exec_())
