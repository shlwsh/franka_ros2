# VCS (vcstool) 配置文件使用指南

当前项目的 VCS 配置文件是根目录下的 **`dependency.repos`**。

这是一个标准的 YAML 格式文件，用于管理多个相关的 Git 仓库依赖。当你需要在工作空间中引入新的代码库时，可以通过修改此文件来实现。

## 如何新增一个 Git 仓库

你可以直接编辑 `dependency.repos` 文件，在 `repositories:` 键下按照相同的格式添加新的条目。格式如下：

```yaml
repositories:
  # ... 已有的仓库 ...
  
  [克隆到本地的目标文件夹名称]:
    type: git
    url: [仓库的 Git URL，例如 https://github.com/xxx/xxx.git]
    version: [分支名、Tag 名或具体的 Commit Hash，例如 main, v1.0.0]
```

### 示例

假设你想添加一个名为 `my_new_pkg` 的包，它需要克隆自 `https://github.com/example/my_new_pkg.git` 的 `jazzy-devel` 分支，你可以将以下内容添加到 `dependency.repos` 的末尾：

```yaml
repositories:
  # ... 原有的配置 ...
  
  my_new_pkg:
    type: git
    url: https://github.com/example/my_new_pkg.git
    version: jazzy-devel
```

## 应用更改 (拉取代码)

添加完成后，你需要使用 `vcs` 命令行工具来读取该文件并拉取（或更新）仓库代码。

在包含该 `.repos` 文件的目录下，或者在你的工作空间的 `src` 目录下运行以下命令：

```bash
vcs import < dependency.repos
```

该命令会读取 `dependency.repos` 中定义的每个仓库，并自动将它们克隆/签出到指定的目录及版本。
