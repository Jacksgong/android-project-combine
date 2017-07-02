from os import listdir, makedirs
from os.path import isdir, exists
from sys import argv

from res_generator import CombineResGenerator
from utils import print_error, process_repos_conf, process_clone_repo, print_process, process_gradle_project_path, \
    print_warn, is_valid_gradle_folder, scan_build_gradle, scan_pom, generate_ignore_matcher, get_default_manifest_path, \
    scan_manifest, process_dependencies, get_default_src_path, handle_process_dependencies, generate_combine_conf_file, \
    generate_combine_manifest_file, generate_combine_gradle_file, generate_mock_res_modules, \
    generate_setting_gradle_file, deeper_source_path

__author__ = 'JacksGong'
__version__ = '1.0.0'
__description__ = 'This python script used for combine several Android projects to one project.'

# ../
root_path = ''
DEFAULT_COMBINE_NAME = 'dev'
combine_name = DEFAULT_COMBINE_NAME
repositories_path = root_path + 'repos/'
repos_conf_path = root_path + 'repos.conf'
combine_project_path = root_path + "combine/" + combine_name
combine_conf_path = root_path + "conf"
combine_gradle_path = combine_conf_path + "/" + combine_name + "-combine.gradle"

print(chr(27) + "[2J")

print("-------------------------------------------------------")
print("Android Project Combine v1.0.0-dev")
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

# handle the conf file.
process_repos_conf(conf_file_path, tmp_repo_addr_list, repo_path_list)
# handle the repo address and get repo_path_list.
process_clone_repo(repositories_path, tmp_repo_addr_list, repo_path_list)
# --------- now repos is ready on repo_path_list


res_group_map = {}
process_dependencies_map = {}
source_dirs = list()
ignored_dependencies_list = list()

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

    for module_dir_name in listdir(project_path):
        module_dir_path = project_path + "/" + module_dir_name

        if not is_valid_gradle_folder(module_dir_name, module_dir_path):
            continue

        # on module folder.

        # scan gradle file.
        gradle_path = module_dir_path + "/build.gradle"
        print_process("scan for " + gradle_path)

        application_id, group_id, artifact_id, dependencies_list = scan_build_gradle(gradle_path)
        # handle dependencies.
        if dependencies_list is not None:
            for dependency_line in dependencies_list:
                process_dependencies(process_dependencies_map, dependency_line)

        # handle src
        src_dir_path = get_default_src_path(module_dir_path)
        if exists(src_dir_path) and isdir(src_dir_path):
            source_dirs.append(src_dir_path)

        # handle res
        # R.xxx dependent on manifest application id.
        manifest_application_id = scan_manifest(get_default_manifest_path(module_dir_path))
        if manifest_application_id is None:
            manifest_application_id = application_id
        if manifest_application_id is None:
            print_warn("can't handle res for " + repo_path + "because we can't find application id from it.")
        else:
            mock_res_path = pom_artifact_id
            if mock_res_path is None:
                mock_res_path = artifact_id
            if mock_res_path is None:
                mock_res_path = manifest_application_id.replace(".", "_")
            res_group_map[manifest_application_id] = mock_res_path

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

# scan res
res_generator = CombineResGenerator()
res_generator.scan(repo_path_list)
res_module_name_list = res_generator.generate(combine_project_path, res_group_map)
generate_combine_conf_file(combine_name, combine_gradle_path, source_dirs, final_dependencies_list,
                           res_module_name_list)

# generate combine project
print_process("generate combine project")
if not exists(combine_project_path):
    makedirs(combine_project_path)
# generate manifest file
generate_combine_manifest_file(combine_project_path, 'cn.dreamtobe.combine.' + combine_name)
# generate gradle file
generate_combine_gradle_file(combine_project_path, combine_name)
# generate the res-modules
generate_mock_res_modules(combine_project_path, res_module_name_list)

# declare to the setting gradle
print_process("declare to the setting gradle")
generate_setting_gradle_file(root_path, combine_project_path, combine_name, res_module_name_list)

print_process("everything is ready, please open the combine project on AndroidStudio!")
