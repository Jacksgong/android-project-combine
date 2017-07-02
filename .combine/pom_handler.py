from os.path import exists
from xml.etree.ElementTree import parse

__author__ = 'JacksGong'
__version__ = '1.0.0'
__description__ = 'This python script used for parsing pom file.'


class PomHandler:
    def __init__(self):
        pass

    groupId = None
    artifactId = None
    dependencies = list()

    def parse(self, pom_file_path):
        if exists(pom_file_path):
            # parse pom.xml
            pom_xml_root = parse(pom_file_path).getroot()

            for child in pom_xml_root:
                if 'groupId' in child.tag:
                    self.groupId = child.text
                if 'artifactId' in child.tag:
                    self.artifactId = child.text
