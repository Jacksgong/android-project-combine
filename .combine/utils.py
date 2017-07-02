import re
import subprocess
from distutils.version import LooseVersion
from os import environ, listdir

from xml.etree.ElementTree import parse

from os.path import exists, isdir


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


# get repo-addr or repo-path from repo_candidate_path
def handle_repo_path(repo_candidate_path, repo_addr_list, repo_path_list):
    if repo_candidate_path.startswith('http') or repo_candidate_path.startswith('git'):
        repo_addr_list.append(repo_candidate_path)
    elif repo_candidate_path.startswith('~') or repo_candidate_path.startswith('/') or repo_candidate_path.startswith(
            '\\'):
        local_path = handle_home_case(repo_candidate_path)
        if exists(local_path):
            repo_path_list.append(local_path)
        else:
            print_warn("The directory of " + repo_candidate_path + " can't found!")
            return False
    else:
        print_warn("can't recognize " + repo_candidate_path + " format!")
        return False
    return True


# check whether the module_candidate_path is module path
def is_valid_gradle_folder(module_candidate_name, module_candidate_path):
    return module_candidate_name != ".DS_Store" and module_candidate_name != ".git" and isdir(
        module_candidate_path) and exists(module_candidate_path + "/build.gradle")


# process the conf_path to get the repo_addr_list and the repo_path_list
def process_repos_conf(conf_path, repo_addr_list, repo_path_list):
    if exists(conf_path):
        # loading config from local config file.
        conf_file = open(conf_path, "r")
        for line in conf_file:
            strip_line = line.strip()
            if strip_line == '' or strip_line[0] == '#':
                continue
            if not handle_repo_path(strip_line, repo_addr_list, repo_path_list):
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
                handle_repo_path(content.strip(), repo_addr_list, repo_path_list)


# clone repo if need.
def process_clone_repo(repositories_path, repo_addr_list, target_path_list):
    repo_name_re = re.compile(r'([^/]*)\.git')
    for repo_addr in repo_addr_list:
        re_name = repo_name_re.search(repo_addr)
        repo_folder_name = re_name.groups()[0]

        repo_path = repositories_path + repo_folder_name
        if exists(repo_path):
            print_warn(
                "because of the directory of " + repo_path + " has already existed, we will not clone it again.")
        else:
            print_process("execute bash: git clone " + repo_addr + " " + repo_path)
            git("clone", repo_addr, repo_path)
            target_path_list.append(repo_path)


# get real project path(which has settings.gradle file)
def process_gradle_project_path(project_candidate_path):
    setting_gradle_path = project_candidate_path + "/settings.gradle"
    if not exists(setting_gradle_path):
        for dir_name in listdir(project_candidate_path):
            # try sub folder
            try_repo_path = project_candidate_path + "/" + dir_name

            try_setting_gradle_path = try_repo_path + "/settings.gradle"
            print_process("try the gradle: " + try_setting_gradle_path)
            if exists(try_setting_gradle_path):
                return try_repo_path
    else:
        return project_candidate_path

    return None


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


# get applicationId,groupId,artifactId,dependencies
def scan_build_gradle(module_build_gradle_path):
    application_id = None
    group_id = None
    artifact_id = None
    dependencies = list()

    if not exists(module_build_gradle_path): return application_id, group_id, artifact_id, dependencies

    group_id_re = re.compile(r'group *= *"(.*) *"')
    artifact_id_re = re.compile(r'artifactId *= *"(.*) *"')
    application_id_re = re.compile(r'applicationId *["|\'](.*) *["|\']')

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
                application_id = search_regex(application_id_re, line)
                if application_id is not None:
                    continue

        if group_id is None:
            group_id = search_regex(group_id_re, line)
            if group_id is not None:
                continue

        if artifact_id is None:
            artifact_id = search_regex(artifact_id_re, line)
            if artifact_id is not None:
                continue

        if not in_dependencies and line.startswith('dependencies'):
            in_dependencies = True
        elif in_dependencies:
            dependencies.append(line)

    gradle_file.close()

    return application_id, group_id, artifact_id, dependencies


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
    artifact_type = None
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

    if dp_type != "provided" and dp_type != "compile":
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
    return module_path + "/src"


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


def generate_combine_conf_file(combine_name, combine_project_path, combine_gradle_path,
                               source_dirs, dependencies_list, res_module_name_list):
    combine_gradle_file = open(combine_gradle_path, "w+")

    combine_gradle_file.write("ext {\n")
    if source_dirs is None or source_dirs.__len__() <= 0:
        combine_gradle_file.write("   javaDirs  = null\n")
    else:
        combine_gradle_file.write("    javaDirs = ")
        combine_gradle_file.write(source_dirs.__str__())

    combine_gradle_file.write("\n")
    #
    # if res_dirs is None or res_dirs.__len__() <= 0:
    combine_gradle_file.write("    resDirs = null\n")
    # else:
    #     combine_gradle_file.write("    resDirs = ")
    #     combine_gradle_file.write(res_dirs.__str__())
    combine_gradle_file.write("\n}")

    project_path = combine_project_path

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
    build_gradle_file.write("apply from: '../../combine-common.gradle'\n")
    build_gradle_file.close()


def generate_mock_res_modules(project_path, res_module_name_list):
    for res_module_name, package_name in res_module_name_list:
        res_module_path = project_path + "/" + res_module_name
        # Android Manifest
        generate_combine_manifest_file(res_module_path, package_name)
        # gradle file
        build_gradle_path = res_module_path + "/" + "build.gradle"
        build_gradle_file = open(build_gradle_path, "w+")
        build_gradle_file.write("apply plugin: 'com.android.library'\n\n")

        # -- res
        build_gradle_file.write("ext {\n")
        build_gradle_file.write("    javaDirs = null")
        build_gradle_file.write("\n}")
        build_gradle_file.write("\napply from: '../../../combine-res-common.gradle'\n")
        build_gradle_file.close()


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


def get_res_mock_module_name(combine_name, res_module_name):
    return combine_name + "-" + res_module_name
