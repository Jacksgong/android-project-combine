# Android Project Combine

![](https://img.shields.io/badge/combine-project-origin.svg)
![](https://img.shields.io/badge/combine-safely-green.svg)
![](https://img.shields.io/badge/combine-easily-green.svg)

> [中文文档](https://github.com/Jacksgong/android-project-combine/blob/master/README-ZH.md)

Combine multiple android projects on one Android Studio window safely and easily, which just mock a combined project contains multiple projects, so you just open combine project on Android Studio to maintain those projects.

## KICK OFF

This demonstrate we using configures on [repos.templete.conf](https://github.com/Jacksgong/android-project-combine/blob/master/repos.templete.conf)(combine [FileDownloader](https://github.com/lingochamp/FileDownloader) project with [filedownloader-okhttp3-connection](https://github.com/Jacksgong/filedownloader-okhttp3-connection) project):

![](https://github.com/Jacksgong/arts/raw/master/android-project-combine/simple-use-en.gif)

Following is the demonstrate to maintain `filedownloader-okhttp3-connection` on android-project-combine:

![](https://github.com/Jacksgong/arts/raw/master/android-project-combine/maintain-en.gif)

> P.S. If above videos can't play，you can click [video1](https://github.com/Jacksgong/arts/raw/master/android-project-combine/simple-use-en.mp4)、[video2](https://github.com/Jacksgong/arts/raw/master/android-project-combine/maintain-en.mp4) to download they manually.

## WHAT ABOUT THIS?

> This is very useful when you developing several projects but they need to communicate each other(such as Atlas project)

- Just a developing env wrapper, it can't modify projects, safe to use.
- Different Android projects develop together at the one Android Studio window.
- Find References and Jump into source code rather than .class file on jar package.
- Jump out of the each projects compile system and using the official compile system.
- Very light, very fast for each time you want to refresh combine project.

## HOW TO USE?

#### Step 1. Create `repos.conf` File

> P.S. You can refer to `/repos.templete.conf`

You need create `repos.conf` file on project root directory, and declare which repo you want to combine on it(one line one repo address).

```yml
# import FileDownloader porject
git@github.com:lingochamp/FileDownloader.git
# declare the FileDownloader exposed arr with groupId:artifactId
- exposed: com.liulishuo.filedownloader:library
# declare ignore the module with its folder name 'demo'
- ignore-module: demo
# declare ignore the module with its folder name 'demo2'
- ignore-module: demo2

# import filedownloader okhttp3 connection project
git@github.com:Jacksgong/filedownloader-okhttp3-connection.git

# import Demo project on ~/Downloads/Demo folder
~/Downloads/Demo
```

> As you can see above, we can recognize repos address and local absolute path.

#### Step 2. Refresh env

Execute `./refresh.sh` to refresh env

![](https://github.com/Jacksgong/arts/raw/master/android-project-combine/refresh-demo.gif)

#### Step 3. Open on the Android Studio

Open android-project-combine on the Android Studio.

![](https://github.com/Jacksgong/arts/raw/master/android-project-combine/android-studio-demo.gif)

## STRUCTURE OF COMBINE PROJECT 

```
.
├── .combine                       // all combine python script folder
│   ├── combine.py                 // scan projects and generated env
│   ├── combine-common.gradle      // common gradle for combine project
│   ├── combine-res-common.gradle  // common gradle for mock resources modules
│   ├── res_generator.py           // scan projects resources and generated mock resources module  
│   ├── res_utils.py               // utils for 'res_generator.py' 
│   └── utils.py                   // utils for 'combine.py'
├── .gitignore                     // we ignored 'repos.conf', 'repos/', 'conf/', 'combine/', 'combine-settings.gradle'
├── clean.sh                       // you can use this shell script to clean combine env safely
├── combine                        // [generated by refresh.sh] mock project which contain all staff of your projects
│   └── dev                        // [generated by refresh.sh] mock combine project which name is 'dev'
│       ├── AndroidManifest.xml   
│       ├── build.gradle          
│       ├── [mock-res-module1]    // mock resources module1
│       ├── ...                   // mock resources module...
│       └── [mock-res-modulen]    // mock resources modulen
├── combine-settings.gradle        // [generated by refresh.sh] declared contain modules, this is include by settings.gradle             
├── conf                           // [generated by refresh.sh] declared the characteristic of combine projects 
│   └── dev-combine.gradle         // [generated by refresh.sh] declared the characteristic of combine project, you can edit it to fix some uncovered error
├── local                          // local module folder, you can do some customzie on this local module
│   ├── AndroidManifest.xml        
│   ├── build.gradle               
│   └── .gitignore                 // we ignored 'src/', 'res/', 'libs/' on local module, so you can do anything you like clearly
├── refresh.sh                     // you can use this shell script to clean and update combine env safely
├── repos                          // store all projects you declared on 'repos.conf' , we don't change anything on this folder and ignored this folder on '.gitignore', so please feel free to maintain your projects on it
│   ├── [your-project-1]           // your project 1
│   |   ├── [project-1-module-1]
│   |   └── [project-1-module-2]
│   ├── [your-project-2]           // your project 2
│   ├── ...                        // your project ...
│   └── [your-project-n]           // your project n
├── repos.conf                     // [added by you]declared which projects you want to combine with together
├── repos.templete.conf            // [demo conf]the templete of 'repos.conf'
└── settings.gradle                // settings.gradle which include 'local' module and 'combine-settings.gradle'
```


## TODO LIST

- [x] Support aidl
- [x] Support buildConfigField on gradle
- [x] Support `-exposed:` to exposed `groud_id` and `artifact_id`
- [x] Support mipmap
- [x] Support `-ignore-module: [folder name]`
- [x] Support recognize Absolute Local Path on 'repos.conf'

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

