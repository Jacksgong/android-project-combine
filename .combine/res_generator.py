#!/usr/bin/python -u

"""
Copyright (C) 2017 Jacksgong(blog.dreamtobe.cn)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

# This python script used for generating mock resources for multiple modules on multiple projects.

import re
from os import makedirs, walk
from os.path import exists, isfile, join
from shutil import copyfile
from xml.etree.ElementTree import Element, SubElement, tostring

from res_utils import assemble_res_package_name_and_path, assemble_src_and_dst_path, \
    assemble_src_and_dst_path_with_folder, add_one_res_value_to_target_map, find_package_name, scan_xml_string, \
    mock_res_file, mock_res_content

PACKAGE_PATH_RE = re.compile(r' *package *(.*) *;')
R_REF = re.compile(r'R\.([a-z]*)\.(\w*)')
R_DIR_REF = re.compile(r'([a-zA-Z_\.]*)\.R\.([a-z]*)\.(\w*)')
IMPORT_PACKAGE = re.compile(r'import (.*).R;')
MITMAP_PATH_RE = re.compile(r'.*res/mipmap-.*dpi')


class CombineResGenerator:
    # package,{{type, [name]}, {type, [name]}}
    def __init__(self):
        pass

    r_res = {}
    # [packagename, src]
    attrs_res = list()
    mipmap_res = list()
    # menu_res = list()
    need_mock_res = True

    def scan(self, path_list):
        r_res = self.r_res

        for repo_path in path_list:
            for subdir, dirs, files in walk(repo_path):
                for file_name in files:

                    if file_name == 'attrs.xml' and subdir.endswith('res/values'):
                        assemble_res_package_name_and_path(subdir, file_name, self.attrs_res)
                        continue

                    if MITMAP_PATH_RE.match(subdir):
                        assemble_res_package_name_and_path(subdir, file_name, self.mipmap_res)
                        continue
                    # if subdir.endswith('res/menu'):
                    #     package_name = find_package_name(subdir)
                    #     res_path = join(subdir, file_name)
                    #     self.menu_res.append([package_name, res_path])
                    #
                    #     string_res_list = scan_xml_string(res_path)
                    #     for r_name in string_res_list:
                    #         add_one_res_value_to_target_map(package_name, 'string', r_name, r_res)
                    #     continue

                    if not file_name.endswith('.java'):
                        continue

                    java_path = join(subdir, file_name)

                    default_r_package = None
                    in_import_area = False
                    in_coding_area = False
                    java_file = open(java_path, "r")
                    is_first_valid_line = True

                    is_in_note_area = False
                    print 'scan R reference on ' + java_path
                    for line in java_file:
                        strip_line = line.strip()
                        if strip_line == '' or strip_line == '\n':
                            continue

                        if strip_line.startswith('/*'):
                            is_in_note_area = True

                        if is_in_note_area and '*/' in strip_line:
                            is_in_note_area = False
                            continue

                        if is_in_note_area:
                            continue

                        if strip_line.startswith('//') or strip_line.startswith('*'):
                            continue

                        if is_first_valid_line:
                            # this line must be the package line.
                            is_first_valid_line = False
                            default_r_package_search = PACKAGE_PATH_RE.search(strip_line)
                            if default_r_package_search is None:
                                exit(
                                    "can't find package declare for line[" + strip_line + "] on java-file: " + java_path)
                            default_r_package = default_r_package_search.groups()[0]

                        if not in_coding_area:
                            in_import = strip_line.startswith('import')
                            if in_import and not in_import_area:
                                in_import_area = True

                            if not in_import and in_import_area:
                                in_import_area = False
                                in_coding_area = True
                        else:
                            package_name = default_r_package
                            r_ref_re_s = R_DIR_REF.findall(strip_line)
                            r_list = list()
                            if r_ref_re_s is not None:
                                for package_name, r_type, r_name in r_ref_re_s:
                                    # package_name, r_type, r_name = r_ref_re.groups()
                                    r_list.append([package_name, r_type, r_name])
                                    # print("contain R [" + package_name + ", " + r_type + ", " + r_name + "]")

                            r_ref_re_s = R_REF.findall(strip_line)
                            if r_ref_re_s is not None:
                                for r_type, r_name in r_ref_re_s:
                                    # r_type, r_name = r_ref_re.groups()
                                    r_list.append([package_name, r_type, r_name])
                                    # print("contain R [" + r_type + ", " + r_name + "]")

                            if r_list.__len__() <= 0:
                                # not R line, pass
                                continue

                            handled_r = list()
                            for package_name, r_type, r_name in r_list:
                                if package_name is None or r_type is None or r_name is None:
                                    # not R line, pass
                                    continue

                                if package_name + r_type + r_name in handled_r:
                                    continue

                                handled_r.append(package_name + r_type + r_name)

                                add_one_res_value_to_target_map(package_name, r_type, r_name, r_res)

                        if in_import_area:
                            r_import = IMPORT_PACKAGE.search(strip_line)
                            if r_import is not None:
                                default_r_package = r_import.groups()[0]

    def generate(self, root_dir, packagename_foldername_map):
        r_module_folder_list = list()
        r_res = self.r_res

        un_duplicate_copy_mapping = list()
        for package_name in r_res:
            if package_name in packagename_foldername_map:
                module_folder_name = packagename_foldername_map[package_name]
            else:
                module_folder_name = package_name.replace(".", "_")

            if module_folder_name not in r_module_folder_list:
                r_module_folder_list.append([module_folder_name, package_name])

            r_module_res_path = root_dir + "/" + module_folder_name + "/res/"
            r_module_values_path = r_module_res_path + "values/"
            if not exists(r_module_values_path):
                makedirs(r_module_values_path)

            r_id_xml_path = r_module_values_path + "ids.xml"
            r_public_xml_path = r_module_values_path + "public.xml"

            r_id_xml = None
            r_public_xml = None

            r_start_value = 0x25000000
            r_type_name_map = r_res[package_name]

            # [ori, dst]
            need_copy_file = list()
            need_close_res_files = list()
            for r_type in r_type_name_map:
                r_name_list = r_type_name_map[r_type]

                if r_type == "id":
                    if r_id_xml is None:
                        r_id_xml = Element('resources')
                else:
                    if r_public_xml is None:
                        r_public_xml = Element('resources')

                for r_name in r_name_list:

                    if r_name == 'class':
                        continue

                    if r_type == "id":
                        print 'add to ids.xml ' + r_name
                        SubElement(r_id_xml, "item", name=r_name, type="id")
                    else:
                        r_start_value += 1
                        id_value = hex(r_start_value)
                        print 'add to public.xml ' + id_value + ', ' + r_name + ', ' + r_type
                        SubElement(r_public_xml, "public", id=id_value, name=r_name, type=r_type)

                        if not self.need_mock_res:
                            continue

                        # generate mock res
                        if r_type == 'drawable':
                            # drawable
                            mock_res_file(r_module_res_path, r_type, r_name,
                                               '<selector xmlns:android="http://schemas.android.com/apk/res/android"/>')
                        elif r_type == 'anim':
                            mock_res_file(r_module_res_path, r_type, r_name,
                                               '<translate xmlns:android="http://schemas.android.com/apk/res/android"/>')
                        elif r_type == 'layout':
                            mock_res_file(r_module_res_path, r_type, r_name,
                                               '<View xmlns:android="http://schemas.android.com/apk/res/android"\n' \
                                               '    android:layout_width="match_parent"\n' \
                                               '    android:layout_height="match_parent"/>')
                        elif r_type == 'xml':
                            mock_res_file(r_module_res_path, r_type, r_name,
                                               '<PreferenceScreen/>')
                        elif r_type == 'raw':
                            mock_res_file(r_module_res_path, r_type, r_name, 'mock')
                        elif r_type == 'color':
                            res_path = mock_res_content(r_module_values_path, 'colors', r_name, '<color name="',
                                                             '">#000</color>')
                            if res_path not in need_close_res_files:
                                need_close_res_files.append(res_path)
                        elif r_type == 'dimen':
                            res_path = mock_res_content(r_module_values_path, 'dimens', r_name, '<dimen name="',
                                                             '">0dp</dimen>')
                            if res_path not in need_close_res_files:
                                need_close_res_files.append(res_path)
                        elif r_type == 'string':
                            res_path = mock_res_content(r_module_values_path, 'strings', r_name,
                                                             '<string name="',
                                                             '">mock</string>')
                            if res_path not in need_close_res_files:
                                need_close_res_files.append(res_path)
                        elif r_type == 'style':
                            res_path = mock_res_content(r_module_values_path, 'styles', r_name, '<style name="',
                                                             '"/>')
                            if res_path not in need_close_res_files:
                                need_close_res_files.append(res_path)
                        elif r_type == 'menu':
                            # assemble_src_and_dst_path_with_folder(r_module_res_path, r_type, r_name, 'xml',
                            #                                       package_name, un_duplicate_copy_mapping,
                            #                                       self.menu_res, need_copy_file)
                            mock_res_file(r_module_res_path, r_type, r_name,
                                          '<menu/>')

                        elif r_type == 'mipmap':
                            assemble_src_and_dst_path_with_folder(r_module_res_path, r_type, r_name, 'png',
                                                                  package_name, un_duplicate_copy_mapping,
                                                                  self.mipmap_res, need_copy_file)
                        elif r_type == "styleable":
                            dst_path = r_module_values_path + 'attrs.xml'
                            assemble_src_and_dst_path(dst_path, 'attrs.xml', package_name, un_duplicate_copy_mapping,
                                                      self.attrs_res, need_copy_file)

            if r_id_xml is not None:
                with open(r_id_xml_path, "w+") as res_file:
                    res_file.write(tostring(r_id_xml, 'utf-8'))

            if r_public_xml is not None:
                with open(r_public_xml_path, "w+") as res_file:
                    res_file.write(tostring(r_public_xml, 'utf-8'))

            for need_close_file_path in need_close_res_files:
                with open(need_close_file_path, "a") as res_file:
                    res_file.write('</resources>')

            for ori_path, dst_path in need_copy_file:
                print "copy [" + ori_path + "] to " + "[" + dst_path + "]..."
                copyfile(ori_path, dst_path)

        return r_module_folder_list

