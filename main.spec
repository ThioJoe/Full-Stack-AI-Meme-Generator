# -*- mode: python ; coding: utf-8 -*-

# HOW TO BUILD EXE USING PYINSTALLER AND THIS SPEC FILE
# If applicable, ensure you are in the correct virtual environment, and ensure that PyInstaller module is installed
# Run the following command in the terminal:   python -m PyInstaller main.spec


# -------------------- SCRIPTING AND TOOLS TO MAKE IT EASIER TO BUILD --------------------
import os
import site

# Set paths
project_directory = os.getcwd() # The base directory of the project, containing the AIMemeGenerator.py file

def get_package_path(package_to_find):
    site_packages_paths = site.getsitepackages()
    for path in site_packages_paths:
        potential_package_path = os.path.join(path, package_to_find)
        if os.path.exists(potential_package_path):
            return potential_package_path
    return None

# Get necessary package paths
stability_sdk_path = get_package_path('stability_sdk')

# Check if icon file exists
if os.path.exists(os.path.join(project_directory, 'icon.ico')):
    icon_path = os.path.join(project_directory, 'icon.ico')
else:
    icon_path = None


# Check if version file exists
if os.path.exists(os.path.join(project_directory, 'VersionInfo.txt')):
    version_info_file_path = os.path.join(project_directory, 'VersionInfo.txt')
else:
    version_info_file_path = None


## For Testing / Debugging
print(f"\n Current Working Directory: {os.getcwd()}\n")
#input("Press Enter to continue...")

# ----------------------------------- PYINSTALLER CORE SPEC FILE CONTENTS -----------------------------------
block_cipher = None
a = Analysis(['AIMemeGenerator.py'],
            pathex=[f'{project_directory}',
                    os.path.join(stability_sdk_path, "interfaces\\src\\tensorizer\\tensors"),
                    os.path.join(stability_sdk_path, "interfaces\\gooseai\\generation"),
                    ],
            binaries=[],
            datas=[(stability_sdk_path, 'stability_sdk')], # Path needs to be added here. If added later even with 'a.datas+=' it will not work, will say other missing modules
            hiddenimports=[
                'stability_sdk', 
                'stability_sdk.client', 
                'stability_sdk.interfaces.gooseai.generation.generation_pb2', 
                'stability_sdk.interfaces.src.tensorizer.tensors.tensors_pb2'
            ],
            hookspath=[],
            hooksconfig={},
            runtime_hooks=[],
            excludes=[],
            win_no_prefer_redirects=False,
            win_private_assemblies=False,
            cipher=block_cipher,
            noarchive=False)

a.datas += [('api_keys_empty.ini', '.\\assets\\api_keys_empty.ini', 'DATA')]
a.datas += [('settings_default.ini', '.\\assets\\settings_default.ini', 'DATA')]


pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,  
        [],
        name='AIMemeGenerator',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=True,
        icon=None,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None ,
        version=version_info_file_path)
