from setuptools import setup
from distutils import sysconfig
from Cython.Distutils import build_ext
from distutils.core import setup
import os
from Cython.Build import cythonize

# https://stackoverflow.com/questions/60284403/change-output-filename-in-setup-py-distutils-extension
class NoSuffixBuilder(build_ext):
    def get_ext_filename(self, ext_name):
        filename = super().get_ext_filename(ext_name)
        suffix = sysconfig.get_config_var('EXT_SUFFIX')
        ext = os.path.splitext(filename)[1]
        return filename.replace(suffix, "") + ext
        
setup(
    name="Discord Bot",
    ext_modules=cythonize(["*.py", "./commands/*.py"], compiler_directives={'language_level' : "3"}, exclude=["setup.py"]),
    cmdclass={"build_ext": NoSuffixBuilder}
)