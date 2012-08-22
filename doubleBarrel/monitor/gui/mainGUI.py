'''
Created on 2012-06-15

@author: Mat
'''
import sys
import os
import io
import logging
from ui import mainUI
from PyQt4 import QtGui, QtCore
from functools import partial
from doubleBarrel.monitor.manager import ServerManager


class PyQtLogHandler(logging.Handler):
    '''
    A custom logging handler object that will write our log to a provided QTextBrowser widget.
    '''
    def __init__(self, destWidget):
        logging.Handler.__init__(self)
        self._destWidget = destWidget

    def emit(self, record):
        try:
            msg = self.format(record)
            self._destWidget.append(msg)
        except(KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


class MainGUI(QtGui.QMainWindow, mainUI.Ui_mainUi):

    SCRIPT_NAME_COLUMN = 0
    STATUS_COLUMN = 1

    def __init__(self, manager=None):
        QtGui.QMainWindow.__init__(self)
        self.setupUi(self)

        self._manager = manager or ServerManager()
        self._servers = {}  # Stores the QTreeWidgetItem as the key and the server as the value.
        self._urlGroups = {}  # Stores the url as the key and the QTreeWidget as the value.
        self._serverLogWidgets = {}

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

        # Reverse the sorting order of the script name column.
        self.serverTree.sortItems(self.SCRIPT_NAME_COLUMN, QtCore.Qt.AscendingOrder)

    def _setupCallbacks(self):
        '''
        Sets up the signal/slot connections for the GUI.
        '''
        # Manage the log display changing from toggling the checkbox.
        self.showLogCheck.toggled.connect(self._setLogVis)

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

        # Connections for the start and stop server buttons.
        self.startServerAction.triggered.connect(self.startServerButtonPressed)
        self.stopServerAction.triggered.connect(self.stopServerButtonPressed)

    def _setDefaults(self):
        '''
        Set the default state of the GUI.
        '''
        # Ensure the log is displayed properly.
        self.showLogCheck.toggled.emit(self.showLogCheck.checkState())

        # Add all of the servers from the manager.
        for server in self._manager.servers():
            self._addServerToTree(server)

        # Update the server statuses.
        self.updateServerStatuses()

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
        self._urlGroups[url] = urlGroup
        return urlGroup

    def _addServerToTree(self, server, updateSelection=False):
        '''
        Adds a server to the tree view. This is separated from the addServerBtnPressed function because it needs to get
        called when the GUI is first initialized.
        '''
        sgObj = server.shotgunObject()

        # Get the serverUrl's tree item and add the server under the URL group.
        serverUrl = sgObj.config.server
        urlGroup = self._urlGroups.get(serverUrl)
        if not urlGroup:
            urlGroup = self._addUrlGroupToTree(serverUrl)

        # Add the serverItem to the urlGroup and to the storage dict.
        scriptName = sgObj.config.script_name
        serverItem = QtGui.QTreeWidgetItem(urlGroup, [scriptName])
        self._servers[serverItem] = server

        # Expand the urlGroup and select the newly added server.
        urlGroup.setExpanded(True)
        if updateSelection:
            # Clear the existing selection first.
            for selectedItem in self.serverTree.selectedItems():
                self.serverTree.setItemSelected(selectedItem, False)
            self.serverTree.setItemSelected(serverItem, True)

        # Add a widget for displaying the server's log.
        self._createServerLogWidget(server)

        return serverItem

    def addServerBtnPressed(self):
        '''
        Triggered when one of the add server buttons is pressed.
        '''
        # Bring up a file dialog to allow the user to select an sg file.
        # Call the manager's addServer function, passing it the sg file.

        title = "Add a Shotgun server file"
        startingDir = os.path.dirname(__file__)
        acceptedFiles = "Shotgun Server Files (*.sg)"
        sgFilepath = QtGui.QFileDialog.getOpenFileName(self, title, startingDir, acceptedFiles)

        if sgFilepath:
            servers = self._manager.addServersFromFile(str(sgFilepath))
            for server in servers:
                self._addServerToTree(server, updateSelection=True)

    def _createServerLogWidget(self, server):
        '''
        Creates an object for displaying the log for the provided server.
        '''
        # Create the widget, add it to the storage dictionary, and hide it by default.
        logDisplayWidget = QtGui.QTextBrowser(self.logDock)
        self._serverLogWidgets[server] = logDisplayWidget
        logDisplayWidget.setVisible(False)

        # Set it up so the server's log gets automatically written to the widget.
        logger = server.logger()
        # Create a PyQtLogHandler for our logger to write to our widget.
        pyqtHandler = PyQtLogHandler(logDisplayWidget)
        logger.addHandler(pyqtHandler)

    def removeServerBtnPressed(self):
        '''
        Triggered when one of the remove server buttons is pressed.
        '''
        selectedItems = self.serverTree.selectedItems()
        for serverItem in selectedItems:
            # Pop the server from the storage dict. This will also remove it.
            server = self._servers.pop(serverItem)
            # Remove it from the tree view.
            serverItem.parent().removeChild(serverItem)
            # Remove it from the manager.
            self._manager.removeServer(server)

        # Remove any urlGroups that are now empty.
        self._purgeUrlGroups()

    def _purgeUrlGroups(self):
        '''
        This goes through all urlGroups and checks that they still have child
        items. If they do not, they will be removed from the GUI and the
        internal storage dictionary.
        '''
        # Create a copy of the urlGroups dict so we can change the items during iteration.
        for url, urlGroup in self._urlGroups.copy().iteritems():
            # If there are no longer any children.
            if not urlGroup.childCount():
                # Remove the urlGroup from the storage dict.
                self._urlGroups.pop(url)
                # Remove it from the tree widget.
                urlGroupIndex = self.serverTree.indexOfTopLevelItem(urlGroup)
                self.serverTree.takeTopLevelItem(urlGroupIndex)

    def updateServerStatuses(self):
        '''
        Updates the status column for each server object.
        '''
        for serverItem, server in self._servers.iteritems():
            # If the server is running, check whether there are any errors.
            if server.isRunning():
                # If there are no errors, add the smiley/yellow icon.
                if not server.hasErrored():
                    status = "Running"
                # If there are errors, add the frown/red icon.
                else:
                    status = "Errored"
            # If the server is not running, add the sleeping/blue icon.
            else:
                status = "Stopped"

            serverItem.setText(self.STATUS_COLUMN, status)

    def startServerButtonPressed(self):
        '''
        Starts the currently selected server(s).
        '''
        for server in self.selectedServers():
            self._manager.startServer(server)
        self.updateServerStatuses()

    def stopServerButtonPressed(self):
        '''
        Stops the currently selected server(s).
        '''
        for server in self.selectedServers():
            self._manager.stopServer(server)
        self.updateServerStatuses()

    def restartServerButtonPressed(self):
        '''
        Restarts the currently selected server(s).
        '''
        for server in self.selectedServers():
            self._manager.restartServer(server)
        self.updateServerStatuses()


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    mainGUI = MainGUI()
    mainGUI.show()
    sys.exit(app.exec_())
