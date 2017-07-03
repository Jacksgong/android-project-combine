# Android Project Combine

Combine multiple android projects on one Android Studio window.

## WHAT ABOUT THIS?

> This is very useful when you developing several projects but they need to communicate each other(such as Atlas project)

- Different Android projects develop together at the one Android Studio window.
- Find References and Jump into source code rather than .class file on jar package.
- Jump out of the each projects compile system and using the official compile system.

## HOW TO USE?

#### Step 1. Create `repos.conf` File

> P.S. You can refer to `/repos.templete.conf`

You need create `repos.conf` file on project root directory, and declare which repo you want to combine on it(one line one repo address).

#### Step 2. Refresh env

Execute `./refresh.sh` to refresh env

#### Step 3. Open on the Android Studio

Open alipay-project-combine on the Android Studio.


## TODO LIST

- [x] Support aidl
- [x] Support buildConfigField on gradle
- [x] Support `-exposed:` to exposed `groud_id` and `artifact_id`
- [x] Support mipmap
- [] Support `-ignore module: [folder name]`

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
