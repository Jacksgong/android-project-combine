import re
from os import walk, makedirs
from os.path import join, exists
from xml.etree.ElementTree import Element, SubElement, tostring

__author__ = 'JacksGong'
__version__ = '1.0.0'
__description__ = 'This python script used for generate res-ids and res-public from several projects.'

R_REF = re.compile(r'R\.([a-z]*)\.(\w*)')
R_DIR_REF = re.compile(r'([a-zA-Z_\.]*)\.R\.([a-z]*)\.(\w*)')
IMPORT_PACKAGE = re.compile(r'import (.*).R;')
IGNORE_PACKAGE_LIST = ['android']


class ResGenerator:
    def __init__(self):
        pass

    # {package_name, {type, [name]}}
    r_res = {}

    def scan(self, root_dir):
        r_res = self.r_res

        for subdir, dirs, files in walk(root_dir):
            for file_name in files:
                if not file_name.endswith('.java'):
                    continue

                java_path = join(subdir, file_name)

                default_r_package = None
                in_import_area = False
                in_coding_area = False
                java_file = open(java_path, "r")

                print 'scan R reference on ' + java_path
                for line in java_file:
                    strip_line = line.strip()
                    if strip_line == '' or strip_line == '\n':
                        continue

                    if strip_line.startswith('//') or strip_line.startswith('*') or strip_line.startswith('@'):
                        continue

                    if not in_coding_area:
                        in_import = strip_line.startswith('import')
                        if in_import and not in_import_area:
                            in_import_area = True

                        if not in_import and in_import_area:
                            in_import_area = False
                            in_coding_area = True
                    else:
                        package_name = default_r_package
                        r_type = None
                        r_name = None
                        r_ref_re = R_DIR_REF.search(strip_line)
                        if r_ref_re is not None:
                            package_name, r_type, r_name = r_ref_re.groups()
                            # print("contain R [" + package_name + ", " + r_type + ", " + r_name + "]")
                        else:
                            r_ref_re = R_REF.search(strip_line)
                            if r_ref_re is not None:
                                r_type, r_name = r_ref_re.groups()
                                # print("contain R [" + r_type + ", " + r_name + "]")

                        if package_name is None or r_type is None or r_name is None:
                            # not R line, pass
                            continue
                        elif package_name in IGNORE_PACKAGE_LIST:
                            # on ignore list
                            continue
                        else:
                            # add if unique
                            if package_name in r_res:
                                unique_type_name_map = r_res[package_name]
                            else:
                                unique_type_name_map = {}
                                r_res[package_name] = unique_type_name_map

                            if r_type in unique_type_name_map:
                                name_list = unique_type_name_map[r_type]
                            else:
                                name_list = list()
                                unique_type_name_map[r_type] = name_list

                            if r_name in name_list:
                                # duplicate, pass
                                continue

                            # add to list
                            name_list.append(r_name)

                    if in_import_area:
                        r_import = IMPORT_PACKAGE.search(strip_line)
                        if r_import is not None:
                            default_r_package = r_import.groups()[0]

    '''
    packagename_foldername_map: {package_name, module_folder_name}
    root_dir
     |- module_folder_name(unique with package_name)
              |- res
                  |- values
                       |- ids.xml
                       |- public.xml
    '''
    def generate(self, root_dir, packagename_foldername_map):
        r_module_folder_list = list()
        r_res = self.r_res
        for package_name in r_res:
            if package_name in packagename_foldername_map:
                module_folder_name = packagename_foldername_map[package_name]
            else:
                module_folder_name = package_name.replace(".", "_")

            if module_folder_name not in r_module_folder_list:
                r_module_folder_list.append([module_folder_name, package_name])

            r_module_values_path = root_dir + "/" + module_folder_name + "/res/values"
            if not exists(r_module_values_path):
                makedirs(r_module_values_path)

            r_id_xml_path = r_module_values_path + "/" + "ids.xml"
            r_public_xml_path = r_module_values_path + "/" + "public.xml"

            r_id_xml = None
            r_public_xml = None

            r_start_value = 0x25000000
            r_type_name_map = r_res[package_name]
            for r_type in r_type_name_map:
                r_name_list = r_type_name_map[r_type]

                if r_type == "id":
                    if r_id_xml is None:
                        r_id_xml = Element('resources')
                else:
                    if r_public_xml is None:
                        r_public_xml = Element('resources')

                for r_name in r_name_list:
                    if r_type == "id":
                        print 'add to ids.xml ' + r_name
                        SubElement(r_id_xml, "item", name=r_name, type="id")
                    else:
                        r_start_value += 1
                        id_value = hex(r_start_value)
                        print 'add to public.xml ' + id_value + ', ' + r_name + ', ' + r_type
                        SubElement(r_public_xml, "public", id=id_value, name=r_name, type=r_type)

            if r_id_xml is not None:
                with open(r_id_xml_path, "w+") as res_file:
                    res_file.write(tostring(r_id_xml, 'utf-8'))

            if r_public_xml is not None:
                with open(r_public_xml_path, "w+") as res_file:
                    res_file.write(tostring(r_public_xml, 'utf-8'))

        return r_module_folder_list
