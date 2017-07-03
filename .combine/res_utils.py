import re
from os import listdir

from os.path import isdir, join, abspath, pardir

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


def assemble_res_package_name_and_path(subdir, file_name, target_list):
    res_path = abspath(join(subdir, pardir))
    parent_path = abspath(join(res_path, pardir))
    package_name = find_package_name_dir_up(parent_path)
    target_list.append([package_name, join(subdir, file_name)])


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
