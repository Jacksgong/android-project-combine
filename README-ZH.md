# Android多Project维护框架

![](https://img.shields.io/badge/combine-project-origin.svg)
![](https://img.shields.io/badge/combine-safely-green.svg)
![](https://img.shields.io/badge/combine-easily-green.svg)

> [English](https://github.com/Jacksgong/android-project-combine)

该框架在需要同时维护多个项目的时候尤为方便，特别如[Atlas的Bundle项目](https://github.com/alibaba/atlas)或者是我之前介绍的[大项目完全解藕项目中的各独立项目](https://blog.dreamtobe.cn/large-project-develop/)。

## 快速预览

这里以协同开发[repos.templete.conf](https://github.com/Jacksgong/android-project-combine/blob/master/repos.templete.conf)中配置([FileDownloader](https://github.com/lingochamp/FileDownloader)与[filedownloader-okhttp3-connection](https://github.com/Jacksgong/filedownloader-okhttp3-connection)两个项目)为案例:

![](https://github.com/Jacksgong/arts/raw/master/android-project-combine/simple-use-zh.gif)

下面是在框架内迭代`filedownloader-okhttp3-connection`的案例:

![](https://github.com/Jacksgong/arts/raw/master/android-project-combine/maintain-zh.gif)

> P.S. 如果上面视频显示不了，可以点击[视频1](https://github.com/Jacksgong/arts/raw/master/android-project-combine/simple-use-zh.mp4)、[视频2](https://github.com/Jacksgong/arts/raw/master/android-project-combine/maintain-zh.mp4)下载视频

## 解决问题

以维护`A`与`B`两个项目为例(假设`A`项目依赖`B`项目):

- 每次在`B`增加/修改代码，都要重新打包到本地仓库，才能再`A`中看到; **低效!**
- 再一些特殊情况下，`B`项目打包后可能没有带源码，只带了去注解的jar包，这样在`A`所有对`B`的引用跳转，都是跳转到去注解的jar包 **可读性差!**
- 查日志的时候，无法确定对应的类到底是在`A`或者`B`，要在两个工程中来回找，**低效!**

## 特点

- 只在开发期使用，对项目透明，**不会对用户项目做任何修改，也无需任何修改** ，执行脚本以后，直接在Android Studio中打开即可，只是封装了一个新的项目包含了需要引入了所有项目，实际上原项目未做任何改动，重新刷新也不会删除用户项目，安全可靠
- 对项目维护，可继续在原项目做git迭代与维护，不会受到`combine`任何影响，`combine`只是一个本地环境的架子而已
- 不同项目如果有引用关系，可以直接跳转，直接引用
- 可以跳出原有项目的编译体系使用现有Android Studio官方的编译体系进行开发
- 简单易用，快捷轻量，只需要编辑一次一行一个仓库拉取地址的配置文件(默认请在根目录的`repos.conf`中编辑)，之后每次只需要直接执行`./refresh.sh`即可


## 如何使用呢?

#### 第一步. Clone这个项目 

首先，你需要clone这个项目，然后进入这个项目目录作为你的工作环境，最简单的方法:

```shell
git clone git@github.com:Jacksgong/android-project-combine.git && cd android-project-combine
```

这样，接下来所有的操作都是在这个项目目录下进行。

#### 第二步. 创建`repos.conf`文件

> P.S. 你可以直接参考`/repos.templete.conf`

你需要在该项目的根目录中创建`repos.conf`文件，并且在其中定义需要一起协同开发的项目仓库地址(一行一个仓库地址)

```yml
# 引入 FileDownloader 项目
git@github.com:lingochamp/FileDownloader.git
# 申明 FileDownloader 对外暴露的arr: groupId:artifactId (默认我们会通过扫引入项目的根目录的pom文件来获取该参数，如果你不是通过pom的方式，推荐在这里直接定义即可)
- exposed: com.liulishuo.filedownloader:library
# 申明需要忽略的module的文件夹名称，这里我们不需要引入文件夹名为'demo'的module
- ignore-module: demo
# 申明需要忽略的module的文件夹名称，这里我们不需要引入文件夹名为'demo2'的module
- ignore-module: demo2

# 引入filedownloader-okhttp3-connection项目
git@github.com:Jacksgong/filedownloader-okhttp3-connection.git

# 引入在'~/Downloads/Demo'目录下的Demo项目
~/Downloads/Demo
```

> 正如你看到的，我们能够识别仓库地址以及本地绝对路径。

#### 第三步. 刷新Combine项目环境

执行`./refresh.sh`来刷新即可。

![](https://github.com/Jacksgong/arts/raw/master/android-project-combine/refresh-demo.gif)

#### 第四步. 在Android Studio中打开

重新在Android Studio中打开android-project-combine即可。

![](https://github.com/Jacksgong/arts/raw/master/android-project-combine/android-studio-demo.gif)

## 温馨小提示

1. 我们不会修改`/repos`目录下的任何文件，因此请放心的维护在`/repos`下面的各种项目；并且`/combine`、`/repos`、`/conf`、`/combine-settings.gradle`、`/repos.conf` 也不会加入到我们的版本管理，因此本地的添加或修改自动生成的combine项目也不会影响`android-project-combine`仓库的版本迭代。
2. 如果切换分支或者引用资源，建议重新执行`./refresh.sh`来更新本地combine环境来刷新资源引用
3. 如果国内下载对应gradle慢，可以考虑在根目录`build.gradle`文件里面的`buildscript{ repositories {`下一行`jcenter()`上一行添加`maven{ url 'http://maven.aliyun.com/nexus/content/groups/public/'}`，以使用阿里的镜像
4. 欢迎大家试用，有任何问题，欢迎提ISSUE，提PR~ 让你多项目维护更加简单!

## 目录结构 

```
.
├── .combine                          // combine python 脚本目录
│   ├── combine.py                    // 用户扫描所有用户项目以及生成combine项目
│   ├── res_generator.py              // 扫描所有用户项目以及生成模拟的资源module
│   ├── res_utils.py                  // 'res_generator.py'的工具集合
│   └── utils.py                      // 'combine.py'的工具集合
├── gradle                            // gradle 脚本目录
│   ├── repositories-default.gradle   // 默认的仓库地址配置
│   ├── combine-common.gradle         // 公用的combine项目gradle脚本
│   └── combine-res-common.gradle     // 公用的模拟的资源module的gradle脚本
├── .gitignore                        // 我们在版本管理中忽略了'repos.conf'、'repos/'、'conf/'、'combine/'、'combine-settings.gradle'
├── clean.sh                          // 你可以使用这个脚本去清理combine项目的环境
├── combine                           // 【由refresh.sh生成】 自动生成的combine项目以及所有模拟的资源项目
│   └── dev                           // 【由refresh.sh生成】 自动生成的名为'dev'的combine项目
│        ├── AndroidManifest.xml   
│        ├── build.gradle          
│        ├── [mock-res-module1]       // 自动生成的资源module1
│        ├── ...                      // 自动生成的资源module...
│        └── [mock-res-modulen]       // 自动生成的资源modulen
├── combine-settings.gradle           // 【由refresh.sh生成】申明需要包含哪些module，该gradle脚本被settings.gradle引用
├── conf                              // 【由refresh.sh生成】申明自动生成的combine项目的各类特性的配置 
│   └── dev-combine.gradle            // 【由refresh.sh生成】申明名为'dev'的combine项目的各类特性配置，你可以通过编辑这个文件来解决一些未覆盖的异常
├── local                             // 本地的module，你可以在这里做一些定制的事情，该module的'src/'、'res/'、'libs/'均没有加入版本管理
│   ├── AndroidManifest.xml        
│   ├── build.gradle               
│   ├── local-build.gradle            // 【需要你添加】本地的buld.gradle文件，用于需要添加一些特殊的配置(如需要依赖一些库不希望刷新后被清理的)
│   ├── build                   
│   └── .gitignore                    // 我们在版本管理中忽略了本地module的'src/'、'res/'、'libs/'
├── refresh.sh                        // 你可以使用这个脚本去刷新并且更新combine项目环境
├── repos                             // 存储所有你在'repos.conf'定义的项目, 我们不会修改或删除这个目录下的任何文件，该目录也没有被加入我们的版本管理，因此你可以放心的在里面维护你的项目
│   ├── [your-project-1]              // 你的项目1
│   |   ├── [project-1-module-1]
│   |   └── [project-1-module-2]
│   ├── [your-project-2]              // 你的项目2
│   ├── ...                           // 你的项目...
│   └── [your-project-n]              // 你的项目n
├── repos.conf                        // 【需要你添加】申明需要一起开发的项目(一行一个项目地址)
├── repos.templete.conf               // 'repos.conf'的demo
├── dependencies-version.conf         // 【你可以添加】 declared which dependencies version you want to force replace
├── dependencies-version.templete.conf// 'dependencies-version.conf'的demo
├── repositories.gradle               // 【你可以添加】你可以通过创建'repositories.gradle'文件来申明仓库
└── settings.gradle                   // 包含了'local'module以及'combine-settings.gradle'的settings.gradle脚本
```

## LICENSE

```
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
```

