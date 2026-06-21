
from file_inspection.impl.extensionDetector import ExtensionDetector
from file_inspection.provider.fileTypeDetectionProvider import FileTypeDetection


def getfileTypeDetection() -> FileTypeDetection:
    return ExtensionDetector()