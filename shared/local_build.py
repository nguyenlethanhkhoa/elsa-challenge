import os
import shutil

build_dir = os.path.join(os.getcwd(), 'build')
if os.path.isdir(build_dir):
    shutil.rmtree(build_dir)

package_dir = os.path.join(os.getcwd(), 'shared_package.egg-info')
if os.path.isdir(package_dir):
    shutil.rmtree(package_dir)

os.system('pip install .')
