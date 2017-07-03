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

import re
from os import listdir, makedirs

from os.path import isdir, join, abspath, pardir, exists, isfile

__author__ = 'JacksGong'

APPLICATION_ID_RE = re.compile(r'applicationId *["|\'](.*) *["|\']')
PACKAGE_NAME_RE = re.compile(r'package *= *["|\'](.*) *["|\']')


# find package name for project.
def find_package_name_dir_up(parent_path):
    for file_name in listdir(parent_path):
        if isdir(file_name):
            continue

        if file_name == 'AndroidManifest.xml':
            for line in open(join(parent_path, file_name), 'r'):
                package_name_re_result = PACKAGE_NAME_RE.search(line)
                if package_name_re_result is not None:
                    return package_name_re_result.groups()[0]

        if file_name == 'build.gradle':
            for line in open(join(parent_path, file_name), 'r'):
                application_id_re_result = APPLICATION_ID_RE.search(line)
                if application_id_re_result is not None:
                    return application_id_re_result.groups()[0]

    return find_package_name_dir_up(abspath(join(parent_path, pardir)))


def find_package_name(subdir):
    res_path = abspath(join(subdir, pardir))
    parent_path = abspath(join(res_path, pardir))
    return find_package_name_dir_up(parent_path)


def assemble_res_package_name_and_path(subdir, file_name, target_list):
    package_name = find_package_name(subdir)
    target_list.append([package_name, join(subdir, file_name)])


def assemble_src_and_dst_path_with_folder(res_root_path, res_type, res_name, res_extension, package_name,
                                          un_duplicate_copy_mapping, marked_res_list, target_list):
    dst_root_path = res_root_path + res_type + '/'
    if not exists(dst_root_path):
        makedirs(dst_root_path)

    file_name = res_name + '.' + res_extension
    dst_path = dst_root_path + file_name
    assemble_src_and_dst_path(dst_path, file_name, package_name, un_duplicate_copy_mapping,
                              marked_res_list, target_list)


def assemble_src_and_dst_path(dst_path, file_name, package_name, un_duplicate_copy_mapping, marked_res_list,
                              target_list):
    if package_name + dst_path in un_duplicate_copy_mapping:
        return

    for marked_package_name, src_path in marked_res_list:
        if package_name == marked_package_name and src_path.endswith(file_name):
            target_list.append([src_path, dst_path])
            un_duplicate_copy_mapping.append(package_name + dst_path)
            marked_res_list.remove([marked_package_name, src_path])
            return


AT_STRING_RE = re.compile(r'="@string/(\w*)"')


def scan_xml_string(xml_path):
    target_list = list()
    xml_file = open(xml_path, 'r')
    for line in xml_file:
        line = line.strip()
        if line.startswith('<'):
            continue
        at_string_finder = AT_STRING_RE.search(line)
        if at_string_finder is not None:
            r_name = at_string_finder.groups()[0]
            target_list.append(r_name)
    xml_file.close()

    return target_list


IGNORE_PACKAGE_LIST = ['android']


def add_one_res_value_to_target_map(package_name, r_type, r_name, target_map):
    if package_name in IGNORE_PACKAGE_LIST:
        return

    if package_name in target_map:
        unique_type_name_map = target_map[package_name]
    else:
        unique_type_name_map = {}
        target_map[package_name] = unique_type_name_map

    if r_type in unique_type_name_map:
        name_list = unique_type_name_map[r_type]
    else:
        name_list = list()
        unique_type_name_map[r_type] = name_list

    if r_name not in name_list:
        name_list.append(r_name)


def mock_res_file(root_path, r_type, value, mock_content):
    res_path = root_path + r_type + "/"
    if not exists(res_path):
        makedirs(res_path)

    target_res_path = res_path + value + '.xml'
    print 'mock ' + target_res_path
    with open(target_res_path, "w+") as res_file:
        res_file.write(mock_content)


def mock_res_content(root_path, type, value, prefix, suffix):
    res_path = root_path + type + ".xml"
    is_first_created = not isfile(res_path)
    print 'mock ' + value + ' on ' + res_path
    if is_first_created:
        with open(res_path, "w+") as res_file:
            # open the resource
            res_file.write('<?xml version="1.0" encoding="utf-8"?>\n')
            res_file.write('<resources>\n')

    with open(res_path, "a") as res_file:
        res_file.write('    ' + prefix + value + suffix + '\n')

    return res_path
