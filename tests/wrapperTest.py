'''
Created on Mar 21, 2012

@author: mat.facer
'''
import os
import string
from ConfigParser import ConfigParser
from doubleBarrel import DoubleBarrel
from shotgun_api3 import Shotgun
from timeit import Timer


class DoubleBarrelTest(object):

    LOOPS = 100
    PRINT_RESULTS = False

    def __init__(self, testClass):
        self._testClass = testClass
        self._testTimes = []

    def testClass(self):
        return self._testClass

    def _getShotgunObject(self):
        '''
        Returns a Shotgun/DoubleBarrel object, depending on what was specified
        when the test class was created.
        '''
        config = ConfigParser()
        dirPath = os.path.dirname(__file__)
        sgFile = os.path.join(dirPath, 'myShotgunScript.sg')
        config.read(sgFile)
        shotgunData = dict(config.items('ShotgunData'))
        serverPath = shotgunData.get('base_url')
        scriptName = shotgunData.get('script_name')
        scriptKey = shotgunData.get('api_key')
        return self.testClass()(serverPath, scriptName, scriptKey)

    def _queryShotgun(self, shotgunObject):
        '''
        Performs the standard test query to Shotgun.
        '''
        return shotgunObject.find('Project', [])

    def testTimes(self):
        '''
        All of the test times, in the order they occurred.
        '''
        return self._testTimes

    def timeHits(self):
        '''
        The number of times a query took said amount of time.
        '''
        roundedTimes = ['%.1f' % testTime for testTime in self.testTimes()]
        uniqueTimes = sorted(list(set(roundedTimes)))
        timeHits = []
        for testTime in uniqueTimes:
            hits = '%s hits' % roundedTimes.count(testTime)
            timeHits.append((testTime, hits))
        return timeHits

    def fastestTime(self):
        return min(self.testTimes())

    def slowestTime(self):
        return max(self.testTimes())

    def medianTime(self):
        '''
        The test time right in the middle of the results.
        '''
        midIndex = int(len(self.testTimes()) / 2)
        return sorted(self.testTimes())[midIndex]

    def _strToInt(self, theString):
        '''
        Converts a string to an int, removing all non numeric characters in
        the process.
        '''
        nonDigitChars = string.printable.translate(None, string.digits)
        return int(theString.translate(None, nonDigitChars))

    def modeTime(self):
        '''
        The time that was most frequent, rounded to the number of decimals.
        '''
        timeHits = self.timeHits()
        # Sort time counts into a dictionary with the counts being the keys.
        hitsDict = {}
        for timeCount in timeHits:
            time, count = timeCount
            count = self._strToInt(count)
            hitsDict.setdefault(count, [])
            hitsDict[count].append(time)
        # Return the list of times with the highest hit count.
        return hitsDict[max(hitsDict.keys())]

    def meanTime(self):
        '''
        The average time each query took.
        '''
        return self.totalTime() / float(self.LOOPS)

    def totalTime(self):
        '''
        Gets the total amount of time the testing took.
        '''
        totalTime = 0
        for testTime in self.testTimes():
            totalTime += testTime
        return totalTime

    def _run(self, funcToTest, loops):
        '''
        This is the generic test function.
        '''
        print "Speed test - Class: %s Function: %s Units: Seconds" % \
            (self.testClass().__name__, funcToTest.__name__)
        for i in range(loops): #@UnusedVariable
            timer = Timer(funcToTest)
            self.testTimes().append(timer.timeit(1))
        print "\tTotal time: %s" % self.totalTime()
        print "\tMean time: %s" % self.meanTime()
        print "\tMedian time: %s" % self.medianTime()
        print "\tMode time(s): %s" % self.modeTime()
        print "\tFastest time: %s" % self.fastestTime()
        print "\tSlowest time: %s" % self.slowestTime()
        print "\tTime hits: %s" % self.timeHits()
        print  # Create a line break to separate this from next tests.


class IndividualQueryTest(DoubleBarrelTest):

    def individualQuery(self):
        '''
        Creates a Shotgun/DoubleBarrel object and does a single query.
        '''
        sg = self._getShotgunObject()
        results = self._queryShotgun(sg)
        if self.PRINT_RESULTS:
            print '\t\t', results

    def run(self):
        self._run(self.individualQuery, self.LOOPS)


class MultipleQueryTest(DoubleBarrelTest):

    def multipleQueries(self):
        '''
        Creates a Shotgun/DoubleBarrel object and does multiple queries.
        '''
        sg = self._getShotgunObject()
        for i in range(self.LOOPS): #@UnusedVariable
            results = self._queryShotgun(sg)
            if self.PRINT_RESULTS:
                print results

    def run(self):
        # Run the timer for one loop since it loops inside the function.
        self._run(self.multipleQueries, 1)


if __name__ == '__main__':
    IndividualQueryTest(DoubleBarrel).run()
    IndividualQueryTest(Shotgun).run()
    MultipleQueryTest(DoubleBarrel).run()
    MultipleQueryTest(Shotgun).run()
