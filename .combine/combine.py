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

from os import listdir, makedirs
from os.path import exists, basename, normpath
from sys import argv

from res_generator import CombineResGenerator
from helper import print_error, process_repos_conf, process_clone_repo, print_process, process_gradle_project_path, \
    print_warn, scan_pom, generate_ignore_matcher, handle_process_dependencies, \
    deeper_source_path, generate_mock_res_modules, generate_build_config_fields_modules, generate_combine_conf_file, \
    generate_combine_manifest_file, generate_combine_gradle_file, generate_setting_gradle_file, scan_module, \
    is_contain_multiple_modules, ROOT_PATH, scan_ext_by_path, process_dep_version_conf

__author__ = 'JacksGong'
__version__ = '1.0.6'
__description__ = 'This python script used for combine several Android projects to one project.'

# ../
DEFAULT_COMBINE_NAME = 'dev'
combine_name = DEFAULT_COMBINE_NAME
repos_conf_path = ROOT_PATH + 'repos.conf'
combine_project_path = ROOT_PATH + "combine/" + combine_name
combine_conf_path = ROOT_PATH + "conf"
combine_gradle_path = combine_conf_path + "/" + combine_name + "-combine.gradle"
ignored_dependencies_list = list()
ignored_modules_list = list()
ext_map = {}

print(chr(27) + "[2J")

print("-------------------------------------------------------")
print("Android Project Combine v" + __version__)
print("-------------------------------------------------------")

# combine_name = raw_input("Please input the name of the combine poject: ")
# if combine_name is None or combine_name.strip() == '':
#     combine_name = DEFAULT_COMBINE_NAME

if exists(combine_project_path):
    print_error(
        "Fatal error: there is the same project with the " + combine_name + " on combine project folder: " +
        combine_project_path)
    exit("Goodbye!")

if argv.__len__() > 1 and argv[1] is not None:
    conf_file_path = argv[1]
else:
    conf_file_path = repos_conf_path

tmp_repo_addr_list = list()
repo_path_list = list()
dep_version_map = {}

# addr/path: [module]
tmp_ignore_modules_map = {}
process_dep_version_conf('dependencies-version.conf', dep_version_map)
# handle the conf file.
process_repos_conf(conf_file_path, tmp_repo_addr_list, repo_path_list, ignored_dependencies_list,
                   tmp_ignore_modules_map)
# handle the repo address and get repo_path_list.
process_clone_repo(tmp_repo_addr_list, repo_path_list, tmp_ignore_modules_map, ignored_modules_list)
# --------- now repos is ready on repo_path_list


res_group_map = {}
process_dependencies_map = {}
source_dirs = list()
aidl_dirs = list()
build_config_fields = {}

for repo_path in repo_path_list:
    print_process("scan for " + repo_path)
    project_path = process_gradle_project_path(repo_path)

    if project_path is None:
        print_warn("can't find valid project on " + repo_path)
        continue

    ignore_dependency = None

    # ---- find output aar/jar groupId and artifactId to ignore
    # 1. scan pom file.
    pom_group_id, pom_artifact_id = scan_pom(project_path + "/pom.xml")
    if pom_group_id is not None and pom_artifact_id is not None:
        ignore_dependency = generate_ignore_matcher(pom_group_id, pom_artifact_id)
        ignored_dependencies_list.append(ignore_dependency)

    if not is_contain_multiple_modules(project_path):
        # current project is just a module
        project_name = basename(normpath(project_path))
        scan_module(repo_path, project_name, project_path, pom_artifact_id, ignored_modules_list,
                    process_dependencies_map, dep_version_map, build_config_fields, source_dirs, aidl_dirs,
                    res_group_map, ext_map)
        continue

    project_gradle_file_path = project_path + '/' + 'build.gradle'
    scan_ext_by_path(project_gradle_file_path, ext_map)

    for module_dir_name in listdir(project_path):
        module_dir_path = project_path + "/" + module_dir_name
        scan_module(repo_path, module_dir_name, module_dir_path, pom_artifact_id, ignored_modules_list,
                    process_dependencies_map, dep_version_map, build_config_fields, source_dirs, aidl_dirs,
                    res_group_map, ext_map)

final_dependencies_list = handle_process_dependencies(process_dependencies_map, ignored_dependencies_list)

print_process("find dependencies: ")
for dependency in final_dependencies_list:
    print dependency

source_dirs = deeper_source_path(source_dirs)
print_process("find source dirs: ")
print source_dirs

# generate combine gradle file
print_process("generate combine gradle file")
print_process("generate " + combine_gradle_path)

# add res and dependencies and source
if not exists(combine_conf_path):
    makedirs(combine_conf_path)

# store all mock modules: [[module_name, application_id]]
mock_module_list = list()

# scan res
res_generator = CombineResGenerator()
res_generator.scan(repo_path_list)
res_module_name_list = res_generator.generate(combine_project_path, res_group_map)
mock_module_list.extend(res_module_name_list)

# generate the res-modules
generate_mock_res_modules(combine_project_path, res_module_name_list, build_config_fields)
# generate the build-config-field-modules
build_config_fields_module_list = generate_build_config_fields_modules(combine_project_path, build_config_fields)
mock_module_list.extend(build_config_fields_module_list)

# generate combine conf file
generate_combine_conf_file(combine_name, combine_gradle_path, source_dirs, aidl_dirs, final_dependencies_list,
                           mock_module_list, ext_map)

# generate combine project
print_process("generate combine project")
if not exists(combine_project_path):
    makedirs(combine_project_path)
# generate manifest file
generate_combine_manifest_file(combine_project_path, 'cn.dreamtobe.combine.' + combine_name)
# generate gradle file
generate_combine_gradle_file(combine_project_path, combine_name)

# declare to the setting gradle
print_process("declare to the setting gradle")
generate_setting_gradle_file(ROOT_PATH, combine_project_path, combine_name, mock_module_list)

print_process("everything is ready, please open the combine project on AndroidStudio!")
