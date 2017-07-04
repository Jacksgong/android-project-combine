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
import subprocess
from distutils.version import LooseVersion
from os import environ, listdir, makedirs
from os.path import exists, isdir
from xml.etree.ElementTree import parse

__author__ = 'JacksGong'


def git(*args):
    return subprocess.check_call(['git'] + list(args))


RESET = '\033[0m'
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)


def termcolor(fg=None, bg=None):
    codes = []
    if fg is not None: codes.append('3%d' % fg)
    if bg is not None: codes.append('10%d' % bg)
    return '\033[%sm' % ';'.join(codes) if codes else ''


def colorize(message, fg=None, bg=None):
    return termcolor(fg, bg) + message + RESET


def print_process(message):
    print colorize(message, fg=GREEN)


def print_error(message):
    print colorize(message, fg=RED)


def print_warn(message):
    print colorize(message, fg=YELLOW)


NO_HOME_PATH = re.compile(r'~/(.*)')
home_path = environ['HOME']


# get the home case path
def handle_home_case(path):
    path = path.strip()
    if path.startswith('~/'):
        path = home_path + '/' + NO_HOME_PATH.match(path).groups()[0]
    return path


EXPOSED_LINE_RE = re.compile(r' *- *exposed: *(.*):(.*)')


def find_exposed_lib(line):
    group_id = None
    artifact_id = None
    finder = EXPOSED_LINE_RE.match(line)
    if finder is None:
        return group_id, artifact_id

    group_id, artifact_id = finder.groups()
    return group_id, artifact_id


IGNORE_MODULE = re.compile(r' *- *ignore-module: *(.*)')


def find_ignore_module(line):
    finder = IGNORE_MODULE.match(line)
    if finder is None:
        return None
    return finder.groups()[0]


def generate_ignore_module_key(repo_path, ignore_module_name):
    return repo_path + ':' + ignore_module_name


class LastRepo:
    def __init__(self):
        pass

    value = None


# get repo-addr or repo-path from repo_candidate_path
def handle_repo_path(repo_candidate_path, repo_addr_list, repo_path_list, ignored_dependencies_list,
                     ignored_modules_map, last_repo):
    group_id, artifact_id = find_exposed_lib(repo_candidate_path)
    if group_id is not None:
        if artifact_id is None:
            print_warn("the format is wrong, we can't find artifact id from " + repo_candidate_path +
                       " right one must be: group_id:artifact_id")
            return False
        ignored_dependencies_list.append(generate_ignore_matcher(group_id, artifact_id))
        print("find need exposed: " + group_id + ":" + artifact_id)
        return True
    elif repo_candidate_path.startswith('http') or repo_candidate_path.startswith('git'):
        last_repo.value = repo_candidate_path
        repo_addr_list.append(repo_candidate_path)
    elif repo_candidate_path.startswith('~') or repo_candidate_path.startswith('/') or repo_candidate_path.startswith(
            '\\'):
        local_path = handle_home_case(repo_candidate_path)
        if exists(local_path):
            last_repo.value = local_path
            repo_path_list.append(local_path)
        else:
            print_warn("The directory of " + repo_candidate_path + " can't found!")
            return False
    else:
        ignore_module = find_ignore_module(repo_candidate_path)
        if ignore_module is not None:
            if last_repo.value is None:
                print_warn("ignore-module must be belong to any repo, wrong format for alone ignore-module " +
                           repo_candidate_path)
                return False
            if last_repo.value not in ignored_modules_map:
                ignored_modules_map[last_repo.value] = list()
            ignore_module_list = ignored_modules_map[last_repo.value]
            ignore_module_list.append(ignore_module)
            print("find ignore module: " + ignore_module + " belong to " + last_repo.value)
            return True

        print_warn("can't recognize " + repo_candidate_path + " format!")
        return False
    return True


# check whether the module_candidate_path is module path
def is_valid_gradle_folder(module_candidate_name, module_candidate_path):
    return module_candidate_name != ".DS_Store" and module_candidate_name != ".git" and isdir(
        module_candidate_path) and exists(module_candidate_path + "/build.gradle")


# process the conf_path to get the repo_addr_list and the repo_path_list
def process_repos_conf(conf_path, repo_addr_list, repo_path_list, ignored_dependencies_list, ignored_modules_map):
    last_repo = LastRepo()
    if exists(conf_path):
        # loading config from local config file.
        conf_file = open(conf_path, "r")
        for line in conf_file:
            strip_line = line.strip()
            if strip_line == '' or strip_line[0] == '#':
                continue
            if not handle_repo_path(strip_line, repo_addr_list, repo_path_list, ignored_dependencies_list,
                                    ignored_modules_map, last_repo):
                exit("Goodbye!")
        conf_file.close()
    else:
        # loading config from hot-input.
        tmp_index = 0
        while True:
            if tmp_index == 0:
                content = raw_input(
                    "Please input the repo address or local repo directory path: ")
            else:
                content = raw_input(
                    "Please continue to input the other repo address or local repo directory path(content/enter "
                    "directly): ")

            tmp_index += 1

            if content is None or content.strip() == '':
                break
            else:
                handle_repo_path(content.strip(), repo_addr_list, repo_path_list, ignored_dependencies_list,
                                 ignored_modules_map, last_repo)


REPO_NAME_RE = re.compile(r'([^/]*)\.git')


# clone repo if need.
def process_clone_repo(repositories_path, repo_addr_list, target_path_list,
                       ignore_modules_map, target_ignore_modules_list):
    # ignore module list
    for repo_path in target_path_list:
        if repo_path in ignore_modules_map:
            ignore_modules_list = ignore_modules_map[repo_path]
            for ignore_module in ignore_modules_list:
                target_ignore_modules_list.append(generate_ignore_module_key(repo_path, ignore_module))

    # clone through git
    for repo_addr in repo_addr_list:
        re_name = REPO_NAME_RE.search(repo_addr)
        repo_folder_name = re_name.groups()[0]

        repo_path = repositories_path + repo_folder_name
        if exists(repo_path):
            print_warn(
                "because of the directory of " + repo_path + " has already existed, we will not clone it again.")
        else:
            print_process("execute bash: git clone " + repo_addr + " " + repo_path)
            git("clone", repo_addr, repo_path)

        # convert ignore module from addr to path
        target_path_list.append(repo_path)
        if repo_addr in ignore_modules_map:
            ignore_modules_list = ignore_modules_map[repo_addr]
            for ignore_module in ignore_modules_list:
                target_ignore_modules_list.append(generate_ignore_module_key(repo_path, ignore_module))


# get real project path(which has settings.gradle file)
def process_gradle_project_path(project_candidate_path):
    setting_gradle_path = project_candidate_path + "/settings.gradle"
    if not exists(setting_gradle_path):
        for dir_name in listdir(project_candidate_path):
            # try sub folder
            try_repo_path = project_candidate_path + "/" + dir_name

            try_setting_gradle_path = try_repo_path + "/settings.gradle"
            print_process("scan settings.gradle file on: " + try_setting_gradle_path)
            if exists(try_setting_gradle_path):
                return try_repo_path
    else:
        return project_candidate_path

    build_gradle_file = project_candidate_path + "/build.gradle"
    if exists(build_gradle_file) and not isdir(build_gradle_file):
        return project_candidate_path

    return None


def is_contain_multiple_modules(project_path):
    return exists(project_path + "/settings.gradle")


# get groupId,artifactId
def scan_pom(pom_file_path):
    group_id = None
    artifact_id = None

    if not exists(pom_file_path): return group_id, artifact_id

    pom_xml_root = parse(pom_file_path).getroot()

    for child in pom_xml_root:
        if 'groupId' in child.tag:
            group_id = child.text
        if 'artifactId' in child.tag:
            artifact_id = child.text
        if group_id is not None and artifact_id is not None:
            break
    return group_id, artifact_id


def search_regex(regex, value):
    regex_re = regex.search(value)
    if regex_re is not None:
        return regex_re.groups()[0]

    return None


# get applicationId,groupId,artifactId,dependencies,build_config_fields
GROUP_ID_RE = re.compile(r'group *= *"(.*) *"')
ARTIFACT_ID_RE = re.compile(r'artifactId *= *"(.*) *"')
APPLICATION_ID_RE = re.compile(r'applicationId *["|\'](.*) *["|\']')
#                                   buildConfigField "boolean", "filed"
BUILD_CONFIG_FIELD_RE = re.compile(r'buildConfigField *"(.*)" *, *"(.*)" *,')


def scan_build_gradle(module_build_gradle_path):
    application_id = None
    group_id = None
    artifact_id = None
    dependencies = list()
    build_config_fields = {}

    if not exists(
            module_build_gradle_path): return application_id, group_id, artifact_id, dependencies, build_config_fields

    in_android_area = False
    in_default_config_area = False
    in_dependencies = False

    gradle_file = open(module_build_gradle_path, 'r')
    for line in gradle_file:
        line = line.strip()

        if application_id is None:
            if not in_android_area and line.startswith('android'):
                in_android_area = True

            if not in_default_config_area and in_android_area and line.startswith('defaultConfig'):
                in_default_config_area = True

            if in_android_area and in_default_config_area:
                application_id = search_regex(APPLICATION_ID_RE, line)
                if application_id is not None:
                    continue
                build_config_field_result = BUILD_CONFIG_FIELD_RE.search(line)
                if build_config_field_result is not None:
                    build_type, build_field = build_config_field_result.groups()
                    build_config_fields[build_field] = build_type

        if group_id is None:
            group_id = search_regex(GROUP_ID_RE, line)
            if group_id is not None:
                continue

        if artifact_id is None:
            artifact_id = search_regex(ARTIFACT_ID_RE, line)
            if artifact_id is not None:
                continue

        if not in_dependencies and line.startswith('dependencies'):
            in_dependencies = True
        elif in_dependencies:
            dependencies.append(line)

    gradle_file.close()

    return application_id, group_id, artifact_id, dependencies, build_config_fields


# get application_id
PACKAGE_RE = re.compile(r'package *= *" *(.*) *"')


def scan_manifest(manifest_path):
    application_id = None
    if not exists(manifest_path):
        return application_id
    else:
        manifest_file = open(manifest_path, "r")
        for line in manifest_file:
            package_result = PACKAGE_RE.search(line)
            if package_result is not None:
                application_id = package_result.groups()[0]
                break
        manifest_file.close()
        return application_id


# parse dependency line
DEPENDENCY_RE1 = re.compile(r"(.*) '(.*):(.*):(.*):(.*)@(.*)'")
DEPENDENCY_RE2 = re.compile(r"(.*) '(.*):(.*):(.*)@(.*)'")
DEPENDENCY_RE3 = re.compile(r"(.*) '(.*):(.*):(.*)'")


def parse_dependency_line(line):
    # dependency_project_re = re.compile(r"(.*) *project\( *'(.*)'\)")

    dp_type = None
    group = None
    artifact = None
    version = None
    artifact_type = ''
    suffix = "aar"

    while True:
        dependency_result = DEPENDENCY_RE1.search(line)
        if dependency_result is not None:
            dp_type, group, artifact, version, artifact_type, suffix = dependency_result.groups()
            break

        dependency_result = DEPENDENCY_RE2.search(line)
        if dependency_result is not None:
            dp_type, group, artifact, version, suffix = dependency_result.groups()
            break

        dependency_result = DEPENDENCY_RE3.search(line)
        if dependency_result is not None:
            dp_type, group, artifact, version = dependency_result.groups()
            break
        # dependency_result = dependency_project_re.search(line)
        # if dependency_result is not None:
        #     dependency_type, artifact = dependency_result.groups()
        #     dependencies_map['undefined' + artifact + 'arr'] = line
        #     break
        break

    return dp_type, group, artifact, version, artifact_type, suffix


def process_dependencies(process_dependencies_map, dependency_line):
    dp_type, group, artifact, version, artifact_type, suffix = parse_dependency_line(dependency_line)
    if dp_type is None:
        return False

    if dp_type == "testCompile":
        # because we didn't support test source tree yet, so we treat its source and dependencies as main.
        dp_type = "compile"
        dependency_line = dependency_line.replace("testCompile", "compile")

    if dp_type != "provided" and dp_type != "compile" and dp_type != "debugCompile" and dp_type != "releaseCompile":
        # on current version we only handle provided and compile.
        return False

    key = group + artifact + suffix + artifact_type

    miss_dependency = None
    new_dependency = None
    if key not in process_dependencies_map:
        process_dependencies_map[key] = [dependency_line, generate_ignore_matcher(group, artifact),
                                         version]
    else:
        pre_dependency_line, pre_ignore_matcher, pre_version = process_dependencies_map[key]
        if LooseVersion(pre_version) < LooseVersion(version):
            process_dependencies_map[key] = [dependency_line, generate_ignore_matcher(group, artifact),
                                             version]
            miss_dependency = pre_dependency_line
            new_dependency = dependency_line
        else:
            new_dependency = pre_dependency_line
            miss_dependency = dependency_line
    if miss_dependency is not None:
        print_warn(
            'loss the dependency ' + miss_dependency + "because of the different version " + new_dependency)

    return True


# get default manifest path
def get_default_manifest_path(module_path):
    manifest_path = module_path + "/src/main/AndroidManifest.xml"
    if exists(manifest_path):
        return manifest_path

    return module_path + "/AndroidManifest.xml"


# get default source path
def get_default_src_path(module_path):
    src_path = module_path + "/src"
    if exists(src_path) and isdir(src_path):
        return src_path
    return None


def get_default_aidl_path(module_path):
    aidl_path = module_path + "/src/main/aidl"
    if exists(aidl_path) and isdir(aidl_path):
        return aidl_path
    aidl_path = module_path + "/aidl"
    if exists(aidl_path) and isdir(aidl_path):
        return aidl_path
    return None


# for generate key for ignore already contained module.
def generate_ignore_matcher(group_id, artifact_id):
    return group_id + ":" + artifact_id


# handle the process dependencies
def handle_process_dependencies(process_dependencies_map, ignored_dependencies_list):
    final_dependencies_list = list()

    for dependency_key in process_dependencies_map:
        real_dependency, ignore_check_param, version = process_dependencies_map[dependency_key]
        valid_dependency = True
        for ignore_dependency in ignored_dependencies_list:
            if ignore_check_param == ignore_dependency or ignore_dependency + '-build' == ignore_check_param:
                valid_dependency = False
                break

        if valid_dependency:
            final_dependencies_list.append(real_dependency)

    return final_dependencies_list


def generate_combine_conf_file(combine_name, combine_gradle_path,
                               source_dirs, aidl_dirs, dependencies_list, res_module_name_list):
    combine_gradle_file = open(combine_gradle_path, "w+")

    combine_gradle_file.write("ext {\n")
    if source_dirs is None or source_dirs.__len__() <= 0:
        combine_gradle_file.write("   javaDirs  = null\n")
    else:
        combine_gradle_file.write("    javaDirs = ")
        combine_gradle_file.write(source_dirs.__str__())

    combine_gradle_file.write("\n")

    if aidl_dirs is None or aidl_dirs.__len__() <= 0:
        combine_gradle_file.write("   aidlDirs  = null\n")
    else:
        combine_gradle_file.write("    aidlDirs = ")
        combine_gradle_file.write(aidl_dirs.__str__())

    combine_gradle_file.write("\n")

    # if res_dirs is None or res_dirs.__len__() <= 0:
    combine_gradle_file.write("    resDirs = null\n")
    # else:
    #     combine_gradle_file.write("    resDirs = ")
    #     combine_gradle_file.write(res_dirs.__str__())
    combine_gradle_file.write("\n}")

    if (dependencies_list is not None and dependencies_list.__len__() > 0) or (
                res_module_name_list.__len__() > 0):
        combine_gradle_file.write("\n")
        combine_gradle_file.write("dependencies {\n")
        for dependency in dependencies_list:
            combine_gradle_file.write("    " + dependency + "\n")

        combine_gradle_file.write("    // ------- res-module ---------\n")
        for res_module_name, package_name in res_module_name_list:
            combine_gradle_file.write(
                "    compile project(':" + get_res_mock_module_name(combine_name, res_module_name) + "')\n")
        combine_gradle_file.write("}")
    combine_gradle_file.close()


def generate_combine_manifest_file(parent_path, package_name):
    manifest_path = parent_path + "/" + "AndroidManifest.xml"
    manifest_file = open(manifest_path, "w+")
    manifest_file.write('<?xml version="1.0" encoding="utf-8"?>\n')
    manifest_file.write('<manifest\n    package="' + package_name + '"/>')
    manifest_file.close()


def generate_combine_gradle_file(project_path, combine_name):
    build_gradle_path = project_path + "/" + "build.gradle"
    build_gradle_file = open(build_gradle_path, "w+")
    build_gradle_file.write("apply plugin: 'com.android.library'\n\n")
    build_gradle_file.write("apply from: '../../conf/" + combine_name + "-combine.gradle'\n")
    build_gradle_file.write("apply from: '../../.combine/combine-common.gradle'\n")
    build_gradle_file.close()


def generate_mock_res_modules(project_path, res_module_name_list, build_config_fields):
    for res_module_name, package_name in res_module_name_list:
        per_build_config_fields = None
        # -- build config field
        if package_name in build_config_fields:
            per_build_config_fields = build_config_fields[package_name]
            # remove it.
            del build_config_fields[package_name]
        generate_mock_module(project_path, res_module_name, package_name, per_build_config_fields)


def generate_build_config_fields_modules(project_path, build_config_fields):
    build_config_fields_module_list = list()
    # -- mock module for build config field.
    for application_id in build_config_fields:
        per_build_config_fields = build_config_fields[application_id]
        if per_build_config_fields.__len__() <= 0:
            continue
        mock_module_name = application_id.replace('.', '_')
        generate_mock_module(project_path, mock_module_name, application_id, per_build_config_fields)
        build_config_fields_module_list.append([mock_module_name, application_id])

    return build_config_fields_module_list


def generate_mock_module(project_path, module_name, package_name, build_config_files):
    module_path = project_path + "/" + module_name
    if not exists(module_path):
        makedirs(module_path)

    # Android Manifest
    generate_combine_manifest_file(module_path, package_name)
    # gradle file
    build_gradle_path = module_path + "/" + "build.gradle"
    build_gradle_file = open(build_gradle_path, "w+")
    build_gradle_file.write("apply plugin: 'com.android.library'\n\n")

    # -- build config field
    if build_config_files is not None and build_config_files.__len__() > 0:
        print("add build config field for " + package_name + " " + build_config_files.__str__())
        fill_build_config_field(build_gradle_file, package_name, build_config_files)

    # -- res
    build_gradle_file.write("ext {\n")
    build_gradle_file.write("    javaDirs = null")
    build_gradle_file.write("\n}")
    build_gradle_file.write("\napply from: '../../../.combine/combine-res-common.gradle'\n")
    build_gradle_file.close()


def fill_build_config_field(build_gradle_file, package_name, per_build_config_fields):
    build_gradle_file.write("android {\n")
    build_gradle_file.write("   defaultConfig {\n")
    for build_field in per_build_config_fields:
        build_type = per_build_config_fields[build_field]
        if build_type == "boolean" or build_type == "Boolean":
            build_gradle_file.write('       buildConfigField "' + build_type + '", "' + build_field + '", "false"\n')
        elif build_type == "String":
            build_gradle_file.write('       buildConfigField "String", "' + build_field + '", "mock"\n')
        else:
            print_warn(
                "we don't support " + build_type + " for build config yet " + "so (" + build_type + " " + build_field +
                ") for " + package_name + " would be ignored!")

    build_gradle_file.write("   }\n}\n")


def generate_setting_gradle_file(root_path, project_path, combine_name, res_module_name_list):
    combine_setting_gradle_path = root_path + "combine-settings.gradle"
    combine_setting_gradle_file = open(combine_setting_gradle_path, "w+")
    combine_setting_gradle_file.write("include ':" + combine_name + "'\n")
    combine_setting_gradle_file.write(
        "project(':" + combine_name + "').projectDir = new File('" + project_path + "')")

    # declare res-module to setting gradle
    for res_module_name, package_name in res_module_name_list:
        res_module_path = project_path + "/" + res_module_name
        res_module_unique_name = get_res_mock_module_name(combine_name, res_module_name)
        combine_setting_gradle_file.write("\ninclude ':" + res_module_unique_name + "'\n")
        combine_setting_gradle_file.write(
            "project(':" + res_module_unique_name + "').projectDir = new File('" + res_module_path + "')")

    combine_setting_gradle_file.close()


def deeper_source_path(source_path_list):
    final_source_path_list = list()
    for source_root_path in source_path_list:
        source_list = assemble_source_path(source_root_path)
        for src in source_list:
            final_source_path_list.append(src)

    return final_source_path_list


def assemble_source_path(source_root_path):
    # todo support read source path from build.gradle.
    source_list = list()

    java_path = source_root_path + "/main/java"
    if exists(java_path) and isdir(java_path):
        source_list.append(java_path)
    kotlin_path = source_root_path + "/main/kotlin"
    if exists(kotlin_path) and isdir(kotlin_path):
        source_list.append(kotlin_path)

    if source_list.__len__() <= 0:
        source_list.append(source_root_path)

    return source_list


def get_res_mock_module_name(combine_name, res_module_name):
    return combine_name + "-" + res_module_name


def scan_module(repo_path, module_dir_name, module_dir_path, pom_artifact_id, ignored_modules_list,
                process_dependencies_map, build_config_fields, source_dirs, aidl_dirs, res_group_map):
    if not is_valid_gradle_folder(module_dir_name, module_dir_path):
        return

    if generate_ignore_module_key(repo_path, module_dir_name) in ignored_modules_list:
        print_warn("ignored " + module_dir_name + " on " + repo_path + " because of you declared on the repos.conf")
        return
    # on module folder.

    # scan gradle file.
    gradle_path = module_dir_path + "/build.gradle"
    print_process("scan for " + gradle_path)

    # R.xxx dependent on manifest application id.
    manifest_application_id = scan_manifest(get_default_manifest_path(module_dir_path))
    application_id, group_id, artifact_id, dependencies_list, per_build_config_fields = scan_build_gradle(
        gradle_path)
    # handle dependencies.
    if dependencies_list is not None:
        for dependency_line in dependencies_list:
            process_dependencies(process_dependencies_map, dependency_line)

    # handle build config field
    build_group_id = application_id
    if build_group_id is None:
        build_group_id = manifest_application_id
    if build_group_id is None:
        print_warn("can't find group id for " + module_dir_path + " we have to give up with it.")
        return

    # todo maybe there are multiple modules with the same build group id
    build_config_fields[build_group_id] = per_build_config_fields

    # handle src
    src_dir_path = get_default_src_path(module_dir_path)
    if src_dir_path is not None:
        source_dirs.append(src_dir_path)

    # handle aidl
    aidl_dir_path = get_default_aidl_path(module_dir_path)
    if aidl_dir_path is not None:
        aidl_dirs.append(aidl_dir_path)

    # handle res
    res_group_id = manifest_application_id
    if res_group_id is None:
        res_group_id = application_id
    if res_group_id is None:
        print_warn("can't handle res for " + module_dir_path + "because we can't find application id from it.")
    else:
        mock_res_path = pom_artifact_id
        if mock_res_path is None:
            mock_res_path = artifact_id
        if mock_res_path is None:
            mock_res_path = manifest_application_id.replace(".", "_")
        res_group_map[manifest_application_id] = mock_res_path
