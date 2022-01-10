import direct.directbase.DirectStart
import time
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
from direct.task import Task

red = (1,0,0,1)
yellow = (1,0.9,0,1)
green = (0,0.9,0,1)


class FPScounter(DirectObject):
    def __init__(self,):
        self.frameTime = 0
        print("Fps Counter starting....")
        base.setBackgroundColor(1, 1, 1)
        self.fpsTextobject = OnscreenText(text=" framerate: " + str(round(self.frameTime))+ " fps", pos=(0.80, 0.90), scale=0.07,bg = (0.3,0.3,0.4,1)) # placeholder
        taskMgr.add(self.fpscounterTask, 'fps1')

        self.fpsTextobject.setFg(green)
        self.maxfps = 144

    def fpscounterTask(self,task):
        self.frameTime = globalClock.getAverageFrameRate()
        #self.frameTime = 30
        color = green
        if self.frameTime <= 144:
            color = green
        if self.frameTime <= 60:
            color = yellow
        if self.frameTime <= 30:
            color = red

        self.fpsTextobject.destroy()
        self.fpsTextobject = OnscreenText(text=" framerate: " + str(round(self.frameTime)) + " fps", pos=(1.03, 0.90),scale=0.07, bg=(0.3, 0.3, 0.4, 1), fg=(color))
        #self.fpsTextobject.setFg(color)

        return task.cont
fpscounter = FPScounter()
run()