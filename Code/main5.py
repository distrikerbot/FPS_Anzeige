import sys
import mmap
import struct
import datetime
import logging
from rich.logging import RichHandler
import time


class SharedMHAMMemoryReader(object):
    """SharedMHAMMemoryReader
    A reinterpreted port of MHAMSharedMemorySample from MSI Afterburner
    from ~\Program Files (x86)\MSI Afterburner\SDK\Samples\SharedMemory

    Connects to a shared Memory Page of MSI Afterburner and extracts the data
    """

    header = dict()
    gpuData = None
    sysData = None
    valid = False

    headerFormat = "@4sIIIIIII"
    headerKeys = ["dwSignature", "dwVersion", "dwHeaderSize", "dwNumEntries",
                  "dwEntrySize", "time", "dwNumGpuEntries", "dwGpuEntrySize"]

    gpuEntryFormat = "@260s260s260s260s260sI"
    gpuEntryKeys = ["szGpuId", "szFamily", "szDevice",
                    "szDriver", "szBIOS", "dwMemAmount"]

    memoryEntryFormat = "@260s260s260s260s260sfffIII"
    memoryEntryKeys = ["szSrcName", "szSrcUnits", "szLocalizedSrcName", "szLocalizedSrcUnits",
                       "szRecommendedFormat", "data", "minLimit", "maxLimit", "dwFlags", "dwGpu", "dwSrcId"]

    def __init__(self, logger):
        self.logger = logger
        self.logger.debug("creating SharedMHAMMemoryReader Instance")

        if not sys.platform.startswith("win"):
            self.logger.error("Shared Memory is only supported on Windows")

    def __checkHeaderSignature(self, header: dict) -> bool:
        if header["dwSignature"].decode("ascii") == "MHAM":
            # header is valid
            self.valid = True
            self.logger.debug("header signature is valid")
            return True
        elif header["dwSignature"].hex() == 0xDEAD:
            # header is marked as dead
            self.valid = False
            self.logger.error("header signature is marked as dead (0xDEAD)")
            return False
        else:
            # memory is uninitialized
            self.valid = False
            self.logger.error("header is uninitilized")
            return None

    def getVersionNum(self) -> (int, int):
        version = self.header.get("dwVersion")
        return (version >> 16, version & 0xFFFF)

    def getVersionStr(self) -> str:
        return "v{0[0]}.{0[1]}".format(self.getVersionNum())

    def getHeader(self) -> dict:
        return self.header

    def getGpuData(self) -> list:
        return self.gpuData

    def getSysData(self) -> list:
        return self.sysData

    def getTimestamp(self) -> int:
        return self.header.get("time", 0)

    def getTime(self) -> str:
        return datetime.datetime.fromtimestamp(self.header.get("time", 0)).isoformat()

    def getSourceAmt(self) -> (int, int):
        return (self.header.get("dwNumEntries"), self.header.get("dwNumGpuEntries"))

    def isDataValid(self) -> bool:
        return self.valid

    def readMemory(self) -> any:
        self.logger.debug("reading memory")
        size = 81920 + 40 * 1024

        try:
            shm = mmap.mmap(-1, size, "Local\\MAHMSharedMemory")
        except Exception as e:
            self.logger.error("failed to open mmap", exc_info=True)
        else:
            try:

                if not shm:
                    # could not open mmap
                    self.logger.error("mmap returned invalid object")
                    return None

                memory = shm.read()

                # header is always 32-bit long (for v2.0)
                headerMem = memory[:32]

                # unpack header into a dict
                headerValues = struct.unpack(self.headerFormat, headerMem)
                self.header = dict(zip(self.headerKeys, headerValues))
                self.logger.debug(self.header)

                if not self.__checkHeaderSignature(self.header):
                    return None

                self.gpuData = list()
                self.sysData = list()

                self.logger.debug(self.getVersionStr())
                if self.getVersionNum()[0] >= 2:
                    for gpuNum in range(0, self.header.get("dwNumGpuEntries")):

                        gpuEntryOffset = self.header.get("dwHeaderSize") + \
                            self.header.get("dwNumEntries") * self.header.get("dwEntrySize") + \
                            gpuNum * self.header.get("dwGpuEntrySize")

                        gpuMemory = memory[gpuEntryOffset:(
                            gpuEntryOffset + self.header.get("dwGpuEntrySize"))]

                        gpuValues = struct.unpack(
                            self.gpuEntryFormat, gpuMemory)
                        gpuDict = dict(zip(self.gpuEntryKeys, gpuValues))

                        for gpuKey in gpuDict.keys():
                            if type(gpuDict[gpuKey]) == bytes:
                                gpuDict[gpuKey] = gpuDict.get(
                                    gpuKey).decode("ascii").rstrip("\x00")

                        print(gpuDict)
                        self.gpuData.append(gpuDict)

                for source in range(self.header.get("dwNumEntries")):
                    offset = self.header.get(
                        "dwHeaderSize") + source * self.header.get("dwEntrySize")

                    entryMemory = memory[offset:(
                        offset + self.header.get("dwEntrySize"))]

                    entryValues = struct.unpack(
                        self.memoryEntryFormat, entryMemory)
                    entry = dict(zip(self.memoryEntryKeys, entryValues))

                    for entryKey in entry.keys():
                        if entryKey.startswith("sz"):
                            # FIXME
                            # "ignore" is import, for whatever reason the ° of temperatures throws an error.
                            # it's encoded as just 0xb0
                            # if it were utf-8 then the start byte of 0xc2 is missing ??
                            # either we're truncating the start byte somewhere (unlinkely since it works with other data fields)
                            # or the encoding is something different ?
                            # https://docs.python.org/3/library/codecs.html#standard-encodings
                            entry[entryKey] = entry.get(entryKey).decode(
                                "utf-8", "ignore").rstrip("\x00")

                    self.sysData.append(entry)

            except Exception as e:
                self.logger.error("Exception occurred", exc_info=True)
            finally:
                shm.close()


if __name__ == "__main__":
    FORMAT = "%(message)s"
    logging.basicConfig(
        level=logging.DEBUG,
        format=FORMAT,
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )

    SharedMHAMMemoryReaderInstance = SharedMHAMMemoryReader(
        logging.getLogger("SharedMHAMMemoryReader"))

    time.sleep(1)

    SharedMHAMMemoryReaderInstance.readMemory()
    for i in SharedMHAMMemoryReaderInstance.getSysData():
        print(i.get("szSrcName"), i.get("data"))

    for i in SharedMHAMMemoryReaderInstance.getGpuData():
        print(i.get("szDevice"), i.get("szFamily"), i.get("dwMemAmount"))

    del SharedMHAMMemoryReaderInstance

