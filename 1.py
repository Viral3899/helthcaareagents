import os
import fnmatch
from pathlib import Path

class TreeGenerator:
    def __init__(self):
        # Directories to exclude
        self.exclude_dirs = [
            'venv',
            'env',
            '.venv',
            '.env',
            'build',
            'dist',
            '*.egg-info',
            'healthcare_management_system.egg-info',
            '__pycache__',
            '.git',
            '.pytest_cache',
            'node_modules',
            '.idea',
            '.vscode',
            '.mypy_cache'
        ]
        
        # File patterns to exclude
        self.exclude_files = [
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '.DS_Store',
            'Thumbs.db',
            '*.log',
            '*.tmp',
            '*.swp',
            '*.swo'
        ]
        
        # Tree drawing characters
        self.PIPE = "│   "
        self.TEE = "├── "
        self.LAST = "└── "
        self.BLANK = "    "
        
        self.file_count = 0
        self.dir_count = 0
        self.excluded_count = 0

    def should_exclude_directory(self, dir_name):
        """Check if directory should be excluded"""
        for pattern in self.exclude_dirs:
            if fnmatch.fnmatch(dir_name, pattern):
                return True
        return False

    def should_exclude_file(self, file_name):
        """Check if file should be excluded"""
        for pattern in self.exclude_files:
            if fnmatch.fnmatch(file_name, pattern):
                return True
        return False

    def get_file_icon(self, filename):
        """Return an icon based on file extension"""
        ext = os.path.splitext(filename)[1].lower()
        icons = {
            '.py': '🐍',
            '.txt': '📄',
            '.md': '📝',
            '.json': '📋',
            '.yml': '⚙️',
            '.yaml': '⚙️',
            '.xml': '📄',
            '.html': '🌐',
            '.css': '🎨',
            '.js': '📜',
            '.sql': '🗄️',
            '.pdf': '📕',
            '.png': '🖼️',
            '.jpg': '🖼️',
            '.jpeg': '🖼️',
            '.gif': '🖼️',
            '.ico': '🖼️',
            '.csv': '📊',
            '.xlsx': '📊',
            '.requirements': '📦',
            '.gitignore': '🚫',
            '.env': '🔐',
            '.ini': '⚙️',
            '.cfg': '⚙️',
            '.conf': '⚙️'
        }
        
        if filename.startswith('.'):
            return '🔧'  # Hidden/config files
        elif filename in ['README.md', 'README.txt', 'README']:
            return '📖'
        elif filename in ['requirements.txt', 'requirements-dev.txt']:
            return '📦'
        elif filename == 'setup.py':
            return '🔧'
        elif filename == 'manage.py':
            return '🎯'
        elif not ext:
            return '📄'  # Files without extension
        
        return icons.get(ext, '📄')

    def build_tree_structure(self, root_path):
        """Build the tree structure recursively"""
        tree_lines = []
        
        def _build_tree(current_path, prefix="", is_last=True):
            items = []
            try:
                for item in os.listdir(current_path):
                    item_path = os.path.join(current_path, item)
                    if os.path.isdir(item_path):
                        if not self.should_exclude_directory(item):
                            items.append((item, item_path, True))  # True for directory
                        else:
                            self.excluded_count += 1
                    else:
                        if not self.should_exclude_file(item):
                            items.append((item, item_path, False))  # False for file
                        else:
                            self.excluded_count += 1
            except PermissionError:
                return
            
            # Sort items: directories first, then files, both alphabetically
            items.sort(key=lambda x: (not x[2], x[0].lower()))
            
            for i, (item_name, item_path, is_dir) in enumerate(items):
                is_last_item = i == len(items) - 1
                
                # Choose the appropriate tree character
                connector = self.LAST if is_last_item else self.TEE
                
                if is_dir:
                    tree_lines.append(f"{prefix}{connector}📁 {item_name}/")
                    self.dir_count += 1
                    
                    # Recursively build subtree
                    extension = self.BLANK if is_last_item else self.PIPE
                    _build_tree(item_path, prefix + extension, is_last_item)
                else:
                    icon = self.get_file_icon(item_name)
                    tree_lines.append(f"{prefix}{connector}{icon} {item_name}")
                    self.file_count += 1
        
        _build_tree(root_path)
        return tree_lines

    def generate_tree(self, root_directory='.', output_file='project_tree.txt'):
        """Generate the complete tree structure"""
        
        # Reset counters
        self.file_count = 0
        self.dir_count = 0
        self.excluded_count = 0
        
        root_path = os.path.abspath(root_directory)
        project_name = os.path.basename(root_path)
        
        print(f"Generating tree structure for: {root_path}")
        print("=" * 60)
        
        # Build tree structure
        tree_lines = self.build_tree_structure(root_path)
        
        # Prepare content for file
        content_lines = []
        content_lines.append("PROJECT TREE STRUCTURE")
        content_lines.append("=" * 60)
        content_lines.append(f"Project: {project_name}")
        content_lines.append(f"Path: {root_path}")
        content_lines.append(f"Generated: {self._get_timestamp()}")
        content_lines.append("=" * 60)
        content_lines.append("")
        content_lines.append(f"📁 {project_name}/")
        
        # Add tree lines with proper indentation
        for line in tree_lines:
            content_lines.append(self.PIPE[:-1] + line)
        
        content_lines.append("")
        content_lines.append("SUMMARY")
        content_lines.append("-" * 20)
        content_lines.append(f"📁 Directories: {self.dir_count}")
        content_lines.append(f"📄 Files: {self.file_count}")
        content_lines.append(f"🚫 Excluded items: {self.excluded_count}")
        content_lines.append(f"📊 Total items: {self.dir_count + self.file_count}")
        
        content_lines.append("")
        content_lines.append("EXCLUDED PATTERNS")
        content_lines.append("-" * 20)
        content_lines.append("Directories:")
        for pattern in self.exclude_dirs:
            content_lines.append(f"  • {pattern}")
        content_lines.append("Files:")
        for pattern in self.exclude_files:
            content_lines.append(f"  • {pattern}")
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            for line in content_lines:
                f.write(line + '\n')
        
        # Print to console
        for line in content_lines[:len(content_lines)-15]:  # Don't print excluded patterns to console
            print(line)
        
        print(f"\n✅ Tree structure saved to: {output_file}")
        return content_lines

    def _get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main():
    """Main function"""
    print("🌳 Healthcare Management System - Tree Structure Generator")
    print("=" * 65)
    
    generator = TreeGenerator()
    
    # Get input parameters
    project_directory = input("Enter project directory path (press Enter for current directory): ").strip()
    if not project_directory:
        project_directory = '.'
    
    output_filename = input("Enter output filename (press Enter for 'project_tree.txt'): ").strip()
    if not output_filename:
        output_filename = 'project_tree.txt'
    
    try:
        if not os.path.exists(project_directory):
            print(f"❌ Error: Directory '{project_directory}' does not exist!")
            return
        
        generator.generate_tree(project_directory, output_filename)
        print(f"\n🎉 Tree generation completed successfully!")
        
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")

if __name__ == "__main__":
    main()