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
- [] Support mipmap
