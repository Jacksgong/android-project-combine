# Android Project Combine

Combine multiple android projects on one Android Studio window.

## WHAT ABOUT THIS?

> This is very useful when you developing several projects but they need to communicate each other(such as Atlas project)

- Just a developing env wrapper, it can't modify projects, safe to use.
- Different Android projects develop together at the one Android Studio window.
- Find References and Jump into source code rather than .class file on jar package.
- Jump out of the each projects compile system and using the official compile system.

## HOW TO USE?

#### Step 1. Create `repos.conf` File

> P.S. You can refer to `/repos.templete.conf`

You need create `repos.conf` file on project root directory, and declare which repo you want to combine on it(one line one repo address).

```yml
# import FileDownloader porject
git@github.com:lingochamp/FileDownloader.git
# declare the FileDownloader exposed arr with groupId:artifactId
- exposed: com.liulishuo.filedownloader:FileDownloader
# declare ignore the module with its folder name 'demo'
- ignore-module: demo
# declare ignore the module with its folder name 'demo2'
- ignore-module: demo2

# import filedownloader okhttp3 connection project
git@github.com:Jacksgong/filedownloader-okhttp3-connection.git
```

#### Step 2. Refresh env

Execute `./refresh.sh` to refresh env

#### Step 3. Open on the Android Studio

Open android-project-combine on the Android Studio.


## TODO LIST

- [x] Support aidl
- [x] Support buildConfigField on gradle
- [x] Support `-exposed:` to exposed `groud_id` and `artifact_id`
- [x] Support mipmap
- [x] Support `-ignore-module: [folder name]`

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
