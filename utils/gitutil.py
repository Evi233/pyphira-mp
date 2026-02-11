import logging
import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Tuple


@dataclass
class GitVersionInfo:
    """Git版本信息数据结构"""
    commit_hash: Optional[str] = None
    short_hash: Optional[str] = None
    branch: Optional[str] = None
    tag: Optional[str] = None
    is_dirty: bool = False
    git_dir: Optional[str] = None
    error: Optional[str] = None
    last_updated: Optional[float] = field(default=None, repr=False)


class GitVersionReader:
    """Git版本读取器"""

    def __init__(self, logger: Optional[logging.Logger] = None, cache_timeout: float = 5.0):
        """
        初始化Git版本读取器
        
        Args:
            logger: 可选的日志记录器，如果未提供则创建默认的
            cache_timeout: 缓存超时时间（秒），默认5秒
        """
        self.logger = logger or self._setup_default_logger()
        self._git_available = self._check_git_availability()
        self._cache_timeout = max(0.1, cache_timeout)  # 最小0.1秒
        self._cache: Dict[str, Tuple[float, GitVersionInfo]] = {}
        self._cache_lock = threading.RLock()  # 线程安全的缓存锁

    def _setup_default_logger(self) -> logging.Logger:
        """设置默认日志记录器"""
        logger = logging.getLogger(f"{__name__}.{id(self)}")
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.WARNING)
        return logger

    def _check_git_availability(self) -> bool:
        """检查git命令是否可用"""
        try:
            result = subprocess.run(
                ['git', '--version'],
                capture_output=True,
                check=True,
                timeout=5
            )
            self.logger.debug("Git command is available")
            return True
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.debug(f"Git command is not available: {e}")
            return False

    def _get_cached_version(self, path: str) -> Optional[GitVersionInfo]:
        """从缓存获取版本信息"""
        with self._cache_lock:
            current_time = time.time()
            if path in self._cache:
                cache_time, version_info = self._cache[path]
                if current_time - cache_time < self._cache_timeout:
                    self.logger.debug(f"Using cached version info for {path}")
                    return version_info
                else:
                    # 缓存过期，删除
                    del self._cache[path]
        return None

    def _cache_version(self, path: str, version_info: GitVersionInfo) -> None:
        """缓存版本信息"""
        with self._cache_lock:
            self._cache[path] = (time.time(), version_info)

    def get_version_info(self, path: str) -> GitVersionInfo:
        """
        获取指定路径的git版本信息
        
        Args:
            path: 要检查的文件或目录路径
            
        Returns:
            GitVersionInfo对象，包含版本信息和可能的错误
        """
        try:
            # 检查缓存
            cached_info = self._get_cached_version(path)
            if cached_info:
                return cached_info

            # 验证输入
            if path is None:
                error_info = GitVersionInfo(error="None path provided")
                self._cache_version(str(path), error_info)
                return error_info

            if not path:
                error_info = GitVersionInfo(error="Empty path provided")
                self._cache_version(path, error_info)
                return error_info

            if not isinstance(path, str):
                error_info = GitVersionInfo(error=f"Invalid path type: {type(path)}")
                self._cache_version(str(path), error_info)
                return error_info

            # 处理网络路径和特殊路径
            normalized_path = self._normalize_path(path)

            # 检查路径是否存在
            if not self._path_exists_safe(normalized_path):
                error_info = GitVersionInfo(error=f"Path does not exist or is not accessible: {path}")
                self._cache_version(path, error_info)
                return error_info

            # 查找git仓库根目录
            git_root = self._find_git_root(normalized_path)
            if not git_root:
                self.logger.debug(f"No git repository found for path: {path}")
                no_git_info = GitVersionInfo()
                self._cache_version(path, no_git_info)
                return no_git_info

            self.logger.debug(f"Found git repository at: {git_root}")

            # 优先使用git命令获取版本信息
            if self._git_available:
                version_info = self._get_version_from_git_command(git_root)
                if version_info and not version_info.error:
                    version_info.last_updated = time.time()
                    self._cache_version(path, version_info)
                    return version_info
                self.logger.debug("Failed to get version from git command, trying direct file read")

            # 回退到直接读取git文件
            version_info = self._get_version_from_git_files(git_root)
            version_info.last_updated = time.time()
            self._cache_version(path, version_info)
            return version_info

        except PermissionError as e:
            error_msg = f"Permission error accessing path: {e}"
            self.logger.error(error_msg)
            error_info = GitVersionInfo(error=error_msg)
            self._cache_version(str(path), error_info)
            return error_info
        except OSError as e:
            error_msg = f"OS error: {e}"
            self.logger.error(error_msg)
            error_info = GitVersionInfo(error=error_msg)
            self._cache_version(str(path), error_info)
            return error_info
        except Exception as e:
            error_msg = f"Unexpected error getting version info: {e}"
            self.logger.error(error_msg, exc_info=True)
            error_info = GitVersionInfo(error=error_msg)
            self._cache_version(str(path), error_info)
            return error_info

    def _normalize_path(self, path: str) -> str:
        """规范化路径，处理网络路径和特殊路径"""
        try:
            # 处理Windows网络路径
            if path.startswith('\\') or path.startswith('//'):
                # 网络路径，直接使用
                return path

            # 处理URL风格路径
            if '://' in path:
                # 可能是smb://, file://等，需要特殊处理
                if path.startswith('smb://') or path.startswith('file://'):
                    return path

            # 处理特殊字符路径
            if '\n' in path or '\t' in path:
                # 清理控制字符
                path = path.replace('\n', '').replace('\t', '')

            # 处理相对路径
            if path == '.':
                path = os.getcwd()
            elif path.startswith('./'):
                path = os.path.join(os.getcwd(), path[2:])

            # 规范化路径
            return os.path.abspath(path)

        except Exception as e:
            self.logger.warning(f"Failed to normalize path {path}: {e}")
            return path

    def _path_exists_safe(self, path: str) -> bool:
        """安全地检查路径是否存在"""
        try:
            # 对于网络路径，直接返回True
            if path.startswith('\\') or path.startswith('//') or '://' in path:
                return True

            # 对于相对路径，先转换为绝对路径
            if path == '.' or path.startswith('./'):
                path = os.path.abspath(path)

            return os.path.exists(path)
        except Exception:
            return False

    def _find_git_root(self, path: str) -> Optional[str]:
        """
        查找git仓库的根目录
        
        Args:
            path: 起始路径
            
        Returns:
            git仓库根目录路径，如果未找到返回None
        """
        try:
            # 处理路径转换的异常情况
            try:
                current_path = Path(path)
                if current_path.is_file():
                    current_path = current_path.parent
            except Exception as e:
                self.logger.debug(f"Error converting path {path}: {e}")
                return None

            # 设置最大遍历深度，防止无限循环
            max_depth = 50
            depth = 0

            # 向上遍历查找.git目录
            while current_path != current_path.parent and depth < max_depth:
                git_dir = current_path / '.git'

                # 检查.git是否存在且可访问
                try:
                    if git_dir.exists():
                        return str(current_path)
                except PermissionError:
                    self.logger.debug(f"Permission denied accessing {git_dir}")
                    # 继续向上查找，不要停止
                except Exception as e:
                    self.logger.debug(f"Error checking {git_dir}: {e}")

                current_path = current_path.parent
                depth += 1

            if depth >= max_depth:
                self.logger.warning(f"Reached maximum traversal depth ({max_depth}) when finding git root")

            return None

        except PermissionError as e:
            self.logger.error(f"Permission error finding git root: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error finding git root: {e}")
            return None

    def _get_version_from_git_command(self, git_root: str) -> Optional[GitVersionInfo]:
        """
        使用git命令获取版本信息
        
        Args:
            git_root: git仓库根目录
            
        Returns:
            GitVersionInfo对象，如果失败返回None
        """
        try:
            # 获取当前提交哈希
            commit_hash = self._run_git_command(git_root, ['rev-parse', 'HEAD'])
            if not commit_hash:
                return None

            # 获取短哈希
            short_hash = self._run_git_command(git_root, ['rev-parse', '--short', 'HEAD'])

            # 获取当前分支
            branch = self._run_git_command(git_root, ['rev-parse', '--abbrev-ref', 'HEAD'])

            # 检查是否有未提交的更改
            is_dirty = bool(self._run_git_command(git_root, ['status', '--porcelain']))

            # 尝试获取标签
            tag = self._run_git_command(git_root, ['describe', '--tags', '--exact-match'])

            return GitVersionInfo(
                commit_hash=commit_hash.strip() if commit_hash else None,
                short_hash=short_hash.strip() if short_hash else None,
                branch=branch.strip() if branch else None,
                tag=tag.strip() if tag else None,
                is_dirty=is_dirty,
                git_dir=os.path.join(git_root, '.git')
            )

        except Exception as e:
            self.logger.error(f"Error getting version from git command: {e}")
            return None

    def _run_git_command(self, git_root: str, command: list) -> Optional[str]:
        """
        运行git命令
        
        Args:
            git_root: git仓库根目录
            command: git命令参数列表
            
        Returns:
            命令输出，如果失败返回None
        """
        try:
            result = subprocess.run(
                ['git', '-C', git_root] + command,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
                encoding='utf-8',
                errors='replace'  # 处理编码错误
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                self.logger.debug(f"Git command failed: {' '.join(command)}, stderr: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            self.logger.debug(f"Git command timed out: {' '.join(command)}")
            return None
        except Exception as e:
            self.logger.debug(f"Error running git command: {e}")
            return None

    def _get_version_from_git_files(self, git_root: str) -> GitVersionInfo:
        """
        通过直接读取git文件获取版本信息
        
        Args:
            git_root: git仓库根目录
            
        Returns:
            GitVersionInfo对象
        """
        try:
            git_dir = os.path.join(git_root, '.git')

            # 检查.git目录类型
            if os.path.isdir(git_dir):
                return self._read_regular_git_repo(git_dir)
            elif os.path.isfile(git_dir):
                return self._read_git_worktree(git_root, git_dir)
            else:
                return GitVersionInfo(error="Invalid git directory structure")

        except Exception as e:
            error_msg = f"Error reading git files: {e}"
            self.logger.error(error_msg)
            return GitVersionInfo(error=error_msg)

    def _read_regular_git_repo(self, git_dir: str) -> GitVersionInfo:
        """
        读取普通git仓库的信息
        
        Args:
            git_dir: .git目录路径
            
        Returns:
            GitVersionInfo对象
        """
        try:
            # 读取HEAD文件
            head_file = os.path.join(git_dir, 'HEAD')
            if not os.path.exists(head_file):
                return GitVersionInfo(error="HEAD file not found")

            with open(head_file, 'r', encoding='utf-8', errors='replace') as f:
                head_content = f.read().strip()

            branch = None
            commit_hash = None

            # 解析HEAD内容
            if head_content.startswith('ref: refs/heads/'):
                branch = head_content.replace('ref: refs/heads/', '')

                # 读取分支引用的提交哈希
                ref_path = head_content.split(' ')[1]
                ref_file = os.path.join(git_dir, ref_path)

                if os.path.exists(ref_file):
                    try:
                        with open(ref_file, 'r', encoding='utf-8', errors='replace') as f:
                            commit_hash = f.read().strip()
                    except Exception as e:
                        self.logger.warning(f"Failed to read ref file {ref_file}: {e}")

            elif len(head_content) == 40 and all(c in '0123456789abcdef' for c in head_content.lower()):
                # 直接是提交哈希
                commit_hash = head_content

            # 生成短哈希
            short_hash = commit_hash[:8] if commit_hash else None

            return GitVersionInfo(
                commit_hash=commit_hash,
                short_hash=short_hash,
                branch=branch,
                git_dir=git_dir
            )

        except PermissionError as e:
            error_msg = f"Permission error reading git repo: {e}"
            self.logger.error(error_msg)
            return GitVersionInfo(error=error_msg)
        except Exception as e:
            error_msg = f"Error reading regular git repo: {e}"
            self.logger.error(error_msg)
            return GitVersionInfo(error=error_msg)

    def _read_git_worktree(self, git_root: str, git_file: str) -> GitVersionInfo:
        """
        读取git worktree的信息
        
        Args:
            git_root: git worktree根目录
            git_file: .git文件路径
            
        Returns:
            GitVersionInfo对象
        """
        try:
            # 读取.git文件内容
            with open(git_file, 'r', encoding='utf-8', errors='replace') as f:
                git_content = f.read().strip()

            if not git_content.startswith('gitdir: '):
                return GitVersionInfo(error="Invalid git worktree file format")

            # 获取实际的git目录
            actual_git_dir = git_content.replace('gitdir: ', '')
            if not os.path.isabs(actual_git_dir):
                actual_git_dir = os.path.join(git_root, actual_git_dir)

            # 验证路径存在
            if not os.path.exists(actual_git_dir):
                return GitVersionInfo(error=f"Git directory not found: {actual_git_dir}")

            # 从实际git目录读取信息
            return self._read_regular_git_repo(actual_git_dir)

        except PermissionError as e:
            error_msg = f"Permission error reading git worktree: {e}"
            self.logger.error(error_msg)
            return GitVersionInfo(error=error_msg)
        except Exception as e:
            error_msg = f"Error reading git worktree: {e}"
            self.logger.error(error_msg)
            return GitVersionInfo(error=error_msg)


def get_git_version(path: str, **kwargs) -> GitVersionInfo:
    """
    便捷的函数接口，获取指定路径的git版本信息
    
    Args:
        path: 要检查的文件或目录路径
        **kwargs: 传递给GitVersionReader的其他参数
        
    Returns:
        GitVersionInfo对象
    """
    reader = GitVersionReader(**kwargs)
    return reader.get_version_info(path)


def format_version_string(version_info: GitVersionInfo,
                          format_str: str = "{short_hash}") -> str:
    """
    格式化版本信息为字符串
    
    Args:
        version_info: GitVersionInfo对象
        format_str: 格式字符串，支持以下占位符：
                   {commit_hash}, {short_hash}, {branch}, {tag}
                   如果信息不可用，占位符会被替换为'unknown'
                   
    Returns:
        格式化后的版本字符串
    """
    if not version_info or version_info.error:
        return "unknown"

    replacements = {
        'commit_hash': version_info.commit_hash or 'unknown',
        'short_hash': version_info.short_hash or 'unknown',
        'branch': version_info.branch or 'unknown',
        'tag': version_info.tag or 'unknown'
    }

    result = format_str
    for key, value in replacements.items():
        result = result.replace(f'{{{key}}}', value)

    return result


def is_git_repository(path: str) -> bool:
    """
    检查路径是否在git仓库中
    
    Args:
        path: 要检查的路径
        
    Returns:
        True如果在git仓库中，否则False
    """
    try:
        info = get_git_version(path)
        return info.commit_hash is not None and info.error is None
    except Exception:
        return False


def get_repository_root(path: str) -> Optional[str]:
    """
    获取git仓库的根目录
    
    Args:
        path: 任意路径
        
    Returns:
        git仓库根目录，如果不在git仓库中返回None
    """
    try:
        info = get_git_version(path)
        if info.git_dir:
            return os.path.dirname(info.git_dir)
        return None
    except Exception:
        return None
